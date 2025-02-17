import os
import nearai
import json
from near_api import NearClient
from typing import Optional, Dict

from nearai.agents.environment import Environment, ThreadMode
from openai.types.beta import Thread
from nearai.shared.models import ThreadMode, RunMode
from supabase import create_client, Client
from datetime import datetime, timedelta

# Supabase Credentials (Make sure to set these environment variables)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize NEAR Client (Replace with your NEAR account details)
near_client = NearClient(
    network=os.getenv("NETWORK"),
    account_id=os.getenv("ACCOUNT_ID"),
    private_key=os.getenv("PRIVATE_KEY")
)

# Initialize AI Agent
agent = nearai.Agent("RentAI", description="AI-powered rent assistant to prevent defaults.")

BASE_PROMPT = "You are a helpful assistant that uses other agents to accomplish tasks."
PROMPTS = {
    "handle_user": f"""{BASE_PROMPT}
If a user starts a new conversation (usually with a hello message), tell them about your capabilities related to rent payments, default prediction, and reminders. Ask them what they need help with.
""",
    "handle_agent": f"""{BASE_PROMPT}
This is a sub-thread, a conversation between you and an agent you have called.
Decide whether the next step is to respond to the agent or to the user.
"""
}

class RentAgent(nearai.Agent):  # Inherit directly from nearai.Agent

    def __init__(self, env: Environment):
        super().__init__("RentAI", description="AI-powered rent assistant to prevent defaults.") # Initialize nearai.Agent
        self.env = env # Initialize env
        self.near_client = near_client
        self.supabase = supabase # Initialize Supabase client

    @agent.function(name="predict_rent_default", description="Predicts rent default risks based on Supabase invoices.")
    def predict_rent_default(self, tenant_id: str) -> str:
        try:
            # Fetch invoices from Supabase
            response = self.supabase.table("invoices").select("*").eq("tenant_id", tenant_id).execute()  # Replace "invoices" with your table name
            invoices = response.data

            if not invoices:
                return f"No invoices found for tenant {tenant_id}."

            overdue_invoices = [inv for inv in invoices if datetime.strptime(inv.get('due_date'), '%Y-%m-%d').date() < datetime.now().date() and inv.get('balance', 0) > 0]  # Check if due_date is past and balance is not zero. Handle missing balance

            if len(overdue_invoices) > 2:
                return f"⚠️ High risk of default for tenant {tenant_id} with {len(overdue_invoices)} overdue invoices."
            else:
                return f"✅ Tenant {tenant_id} is in good standing with {len(overdue_invoices)} overdue invoices."

        except ValueError as e: # Handle date parsing errors
            return f"Error: Invalid date format in invoice data: {e}"
        except Exception as e:
            return f"Error predicting default: {e}"


    @agent.function(name="send_rent_reminder", description="Sends rent reminders before due date.")
    def send_rent_reminder(self, tenant_id: str, due_date_str: str) -> str:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            reminder_date = due_date - timedelta(days=2)
            now = datetime.now().date()

            if now == reminder_date:
                return f"📅 Reminder: Rent due on {due_date.strftime('%Y-%m-%d')} for {tenant_id}. Please pay on time."
            elif now < reminder_date:
                return f"Reminder for {tenant_id} is scheduled for {reminder_date.strftime('%Y-%m-%d')}"
            else:
                return f"Reminder for {tenant_id} was already sent on {reminder_date.strftime('%Y-%m-%d')}"

        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD."
        except Exception as e:
            return f"Error sending reminder: {e}"

    def discovery(self, user_message: str) -> Optional[str]:
        return None  # No other agents discovered for now

    def process_user_message(self, thread):
        prompt = {"role": "system", "content": PROMPTS["handle_user"]}
        user_message = self.env.get_last_message()["content"]
        selected_agent = self.discovery(user_message)

        if selected_agent:
            self.env.add_reply(f"Calling specialized agent: {selected_agent}")
            self.env.run_agent(selected_agent, query=user_message, thread_mode=ThreadMode.CHILD, run_mode=RunMode.WITH_CALLBACK)
            self.env.request_agent_input()
        else:
            result = self.env.completion([prompt] + self.env.list_messages())
            self.env.add_reply(result)
            self.env.request_user_input()

    def process_service_agent_message(self, subthread):
        prompt = {"role": "system", "content": PROMPTS["handle_agent"]}
        parent_thread = subthread.metadata.get("parent_id")
        agent_to_agent_conversation = self.env.list_messages()
        last_message = agent_to_agent_conversation[-1]

        if not last_message or not last_message.get("content"):
            self.env.add_reply("Sorry, something went wrong. Conversation with Service Agent was empty.")
            return

        result = self.env.completion([prompt] + agent_to_agent_conversation)
        self.env.add_reply(result, thread_id=parent_thread)
        self.env.request_user_input()


    def run(self):
        thread = self.env.get_thread()
        parent_id: Thread = thread.metadata.get("parent_id")

        if parent_id:
            self.process_service_agent_message(thread)
        else:
            self.process_user_message(thread)


# Deploy AI Agent
if globals().get('env', None):
    rent_agent = RentAgent(globals().get('env'))
    rent_agent.run()

agent.deploy() # Deploy outside the if block