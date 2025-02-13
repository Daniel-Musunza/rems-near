import os
import nearai
from flask import Flask, request, jsonify
from supabase import create_client, Client

# Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Flask API
app = Flask(__name__)

# AI-Powered Inquiry Handling
def get_response(user_message):
    user_message_lower = user_message.lower()

    # Example: Handling rent-related inquiries
    if "rent status" in user_message_lower:
        tenant_id = user_message.split()[-1]
        response = supabase.table("agreements").select("tenant_id, status").eq("tenant_id", tenant_id).single().execute()

        if response.data:
            return f"Tenant {response.data['tenant_id']}'s agreement status is {response.data['status']}."
        return "No rent agreement found for this tenant."

    # AI-Powered Decision Making: Prevent rent defaults
    elif "rent due" in user_message_lower:
        tenant_id = user_message.split()[-1]
        response = supabase.table("agreements").select("tenant_id, payment_due_date").eq("tenant_id", tenant_id).single().execute()

        if response.data:
            return f"Tenant {response.data['tenant_id']} has rent due on {response.data['payment_due_date']}."
        return "No rent due data found."

    else:
        return "Sorry, I can't find an answer to that."

@app.route("/ask", methods=["POST"])
def handle_user_message():
    data = request.json
    user_message = data.get("message", "")
    response = get_response(user_message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
