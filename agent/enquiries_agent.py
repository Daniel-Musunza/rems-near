import os
import json
from typing import Optional, Dict

from nearai.agents.environment import Environment, ThreadMode
from openai.types.beta import Thread
from nearai.shared.models import ThreadMode, RunMode
from supabase import create_client, Client

# Supabase Credentials (Make sure to set these environment variables)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE_PROMPT = "You are a helpful real estate assistant that often calls other assistant agents to accomplish tasks for the user."
PROMPTS = {
    "handle_user": f"""{BASE_PROMPT}
If a user starts a new conversation (usually with a hello message), tell them about your capabilities in real estate and ask them what they need help with. Mention that you can help with buying, selling, or renting properties, as well as provide information about neighborhoods, market trends, and mortgage options. Come up with a simple initial answer and also formulate a plan based on the user's initial query.
""",
    "handle_agent": f"""{BASE_PROMPT}
This is a sub-thread, a conversation between you and an agent you have called.
Decide whether the next step is to respond to the agent or to the user. Consider the information the agent has provided and whether it addresses the user's needs. If more information is needed, formulate a specific request for the agent. If the user's needs are met, summarize the findings for the user.
"""
}


class RealEstateAgent:

    def __init__(self, env: Environment):
        self.env = env

    def discovery(self, user_message: str) -> Optional[str]:
        """Placeholder for discovery calls."""
        return None

    def fetch_faqs(self):
        """Fetch FAQs from Supabase."""
        try:
            response = supabase.table("faqs").select(
                "*").execute()  # Replace "faqs" with your table name
            if response.data:
                return response.data
            return "No FAQs found."
        except Exception as e:
            return f"Error fetching FAQs: {e}"

    def fetch_property_info(self, filters=None):
        """Fetch properties from Supabase with optional filters."""
        try:
            # Replace "properties" with your table name
            query = supabase.table("properties").select("*")
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = query.execute()

            if response.data:
                return response.data
            return "No properties found matching your criteria."
        except Exception as e:
            return f"Error fetching properties: {e}"

    def fetch_tenant_by_name(self, first_name, last_name):
        """Fetch tenant ID by name from Supabase."""
        try:
            response = supabase.table("tenants").select("id").eq("first_name", first_name).eq(
                # Replace "tenants" with your table name
                "last_name", last_name).single().execute()
            if response.data:
                return response.data["id"]
            return "Tenant not found."
        except Exception as e:
            return f"Error fetching tenant: {e}"

    def fetch_rent_status(self, tenant_id):
        """Fetch rent payment status from Supabase."""
        try:
            response = supabase.table("rentagreements").select("tenant_id, status, payment_due_date").eq(
                # Replace "rentagreements" with your table name
                "tenant_id", tenant_id).single().execute()
            if response.data:
                return f"Tenant {tenant_id} has rent status: {response.data['status']}, due on {response.data['payment_due_date']}."
            return "No rent agreement found."
        except Exception as e:
            return f"Error fetching rent status: {e}"

    def fetch_booking_status(self, tenant_id):
        """Fetch booking status from Supabase."""
        try:
            response = supabase.table("bookings").select("tenant_id, status").eq(
                # Replace "bookings" with your table name
                "tenant_id", tenant_id).execute()
            if response.data:
                return f"Booking status: {response.data[0]['status']}"
            return "No active bookings found."
        except Exception as e:
            return f"Error fetching booking status: {e}"

    def fetch_payment_history(self, tenant_id):
        """Retrieve payment history from Supabase."""
        try:
            response = supabase.table("payments").select("amount, status, date").eq(
                # Replace "payments" with your table name
                "tenant_id", tenant_id).execute()
            if response.data:
                payments = response.data
                if payments:  # Check if there are any payments
                    return f"Latest payment: {payments[-1]['amount']} {payments[-1]['status']} on {payments[-1]['date']}"
                else:
                    return "No payment history found."  # Handles if there are no payments
            return "No payment history found."
        except Exception as e:
            return f"Error fetching payment history: {e}"

    def process_user_message(self, thread):
        """Handles user messages and calls Supabase functions."""
        prompt = {"role": "system", "content": PROMPTS["handle_user"]}
        user_message = self.env.get_last_message()["content"]
        selected_agent = self.discovery(user_message)

        if selected_agent:
            self.env.add_reply(f"Calling specialized agent: {selected_agent}")
            self.env.run_agent(selected_agent, query=user_message,
                               thread_mode=ThreadMode.CHILD, run_mode=RunMode.WITH_CALLBACK)
            self.env.request_agent_input()
        else:
            filters = {}  # Initialize filters

            if "available properties" in user_message.lower() or "list properties" in user_message.lower() or "vacant" in user_message.lower() or "rentals" in user_message.lower():
                if "location" in user_message.lower():
                    try:
                        location = user_message.split("location")[-1].strip()
                        filters["location"] = location
                    except IndexError:
                        pass
                if "bedrooms" in user_message.lower():
                    try:
                        bedrooms = int(user_message.split(
                            "bedrooms")[-1].strip())
                        filters["bedrooms"] = bedrooms
                    except (ValueError, IndexError):
                        pass
                if "min_rent" in user_message.lower():
                    try:
                        min_rent = int(user_message.split(
                            "min_rent")[-1].strip())
                        filters["rent"] = {"gte": min_rent}
                    except (ValueError, IndexError):
                        pass
                if "max_rent" in user_message.lower():
                    try:
                        max_rent = int(user_message.split(
                            "max_rent")[-1].strip())
                        if "rent" in filters:
                            filters["rent"]["lte"] = max_rent
                        else:
                            filters["rent"] = {"lte": max_rent}
                    except (ValueError, IndexError):
                        pass

                response = self.fetch_property_info(filters)

            elif "rent status" in user_message.lower() or "rent agreement" in user_message.lower():
                try:
                    tenant_identifier = user_message.split()[-1]
                    if tenant_identifier.isdigit():
                        tenant_id = int(tenant_identifier)
                    else:
                        parts = tenant_identifier.split()
                        if len(parts) >= 2:
                            first_name = parts[0]
                            last_name = parts[1]
                            tenant_id = self.fetch_tenant_by_name(
                                first_name, last_name)
                        else:
                            response = "Please provide both first and last name for tenant search."
                            self.env.add_reply(response)
                            self.env.request_user_input()
                            return  # Exit early
                    # Check if tenant_id is an integer (from name lookup)
                    if isinstance(tenant_id, int):
                        response = self.fetch_rent_status(tenant_id)
                    else:
                        response = tenant_id  # Error message from name lookup

                except IndexError:
                    response = "Please provide a tenant ID or name."

            elif "booking status" in user_message.lower():
                try:
                    tenant_identifier = user_message.split()[-1]
                    if tenant_identifier.isdigit():
                        tenant_id = int(tenant_identifier)
                    else:
                        parts = tenant_identifier.split()
                        if len(parts) >= 2:
                            first_name = parts[0]
                            last_name = parts[1]
                            tenant_id = self.fetch_tenant_by_name(first_name, last_name)
                        else:
                            response = "Please provide both first and last name for tenant search."
                            self.env.add_reply(response)
                            self.env.request_user_input()
                            return
                    if isinstance(tenant_id, int):
                        response = self.fetch_booking_status(tenant_id)
                    else:
                        response = tenant_id

                except IndexError:
                    response = "Please provide a tenant ID or name."

            elif "payment history" in user_message.lower():
                try:
                    tenant_identifier = user_message.split()[-1]
                    if tenant_identifier.isdigit():
                        tenant_id = int(tenant_identifier)
                    else:
                        parts = tenant_identifier.split()
                        if len(parts) >= 2:
                            first_name = parts[0]
                            last_name = parts[1]
                            tenant_id = self.fetch_tenant_by_name(first_name, last_name)
                        else:
                            response = "Please provide both first and last name for tenant search."
                            self.env.add_reply(response)
                            self.env.request_user_input()
                            return
                    if isinstance(tenant_id, int):
                        response = self.fetch_payment_history(tenant_id)
                    else:
                        response = tenant_id

                except IndexError:
                    response = "Please provide a tenant ID or name."

            elif "faqs" in user_message.lower() or "faq" in user_message.lower() or "questions" in user_message.lower():
                response = self.fetch_faqs()

            else:
                result = self.env.completion([prompt] + self.env.list_messages())
                response = result

            self.env.add_reply(response)
            self.env.request_user_input()

    def process_service_agent_message(self, subthread):
        prompt = {"role": "system", "content": PROMPTS["handle_agent"]}
        parent_thread = subthread.metadata.get("parent_id")
        agent_to_agent_conversation = self.env.list_messages()
        last_message = agent_to_agent_conversation[-1]

        if not last_message or not last_message.get("content"):
            self.env.add_reply("Sorry, something went wrong. Conversation with Service Agent was empty.", thread_id=parent_thread)
            self.env.request_user_input()
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


if globals().get('env', None):
    agent = RealEstateAgent(globals().get('env'))
    agent.run()