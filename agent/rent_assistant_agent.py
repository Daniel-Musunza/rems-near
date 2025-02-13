import os
import nearai
import json
from near_api import NearClient

# Initialize NEAR Client (Replace with your NEAR account details)
near_client = NearClient(
    network= os.getenv("NETWORK"),
    account_id= os.getenv("ACCOUNT_ID"),
    private_key= os.getenv("PRIVATE_KEY")
)

# Initialize AI Agent
agent = nearai.Agent("RentAI", description="AI-powered rent assistant to prevent defaults.")

# Function to check rent payment history & predict defaults
@agent.function(name="predict_rent_default", description="Predicts rent default risks based on NEAR payments.")
def predict_rent_default(tenant_id: str) -> str:
    response = near_client.view_contract_function(
        contract_id="your-contract.testnet",
        method_name="get_agreements",
        args={}
    )
    
    agreements = json.loads(response)
    missed_payments = sum(1 for a in agreements if a['tenantId'] == tenant_id and a['status'] == "Overdue")
    
    if missed_payments > 2:
        return f"⚠️ High risk of default for tenant {tenant_id}."
    
    return f"✅ Tenant {tenant_id} is in good standing."

# Function to automate rent reminders
@agent.function(name="send_rent_reminder", description="Sends rent reminders before due date.")
def send_rent_reminder(tenant_id: str, due_date: str) -> str:
    return f"📅 Reminder: Rent due on {due_date} for {tenant_id}. Please pay on time."

# Deploy AI Agent
agent.deploy()
