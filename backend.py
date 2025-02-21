from flask import Flask, request, jsonify
import psycopg2
import os
import json
import string
import groq

app = Flask(__name__)

# PostgreSQL Connection Details (Replace with your actual credentials)
DB_NAME = "voicebot_db"  # Your newly created database
DB_USER = "your_username"  # Your PostgreSQL username
DB_PASSWORD = "your_password"  # Your PostgreSQL password
DB_HOST = "localhost"
DB_PORT = "5432"  # Default PostgreSQL port


# Establish a database connection
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print("✅ Connected to PostgreSQL")
except Exception as e:
    print("❌ Database Connection Error:", e)
    exit(1)

# Initialize Groq Client securely
GROQ_API_KEY = "your_groq_api_key"  # Replace with your actual API key
client = groq.Client(api_key=GROQ_API_KEY)

def fetch_faq_response(query):
    """Fetch an FAQ response from PostgreSQL."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT answer FROM faqs WHERE question ILIKE %s", (query,))
        result = cur.fetchone()
        cur.close()
        return result[0] if result else None
    except Exception as e:
        print("❌ PostgreSQL Error:", e)
        return None

def fetch_account_info(user_query):
    """Fetch account details for specific queries like 'account balance'."""
    if "account balance" in user_query:
        return "Your current balance is $2,500."
    elif "last transaction" in user_query:
        return "Your last transaction was $150 at XYZ Store."
    return None

def fetch_ai_response(query, chat_history):
    """Fetch response from AI (Groq) with chat history."""
    history_messages = [{"role": "user", "content": msg[0]} for msg in chat_history]
    history_messages += [{"role": "assistant", "content": msg[1]} for msg in chat_history]
    history_messages.append({"role": "user", "content": query})  

    print(f"📝 Sending to AI model: {query}")
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=history_messages,
            temperature=0.7,
        )
        ai_response = response.choices[0].message.content.strip()
        print(f"✅ AI Response: {ai_response}")
        return ai_response
    except Exception as e:
        print("❌ AI Error:", e)
        return "I'm sorry, I couldn't fetch an AI response."

@app.route("/query", methods=["POST"])
def query_handler():
    """Handles user queries and returns a response based on intent."""
    data = request.json
    user_query = data.get("query", "").strip().lower()
    chat_history = data.get("chat_history", [])  

    print(f"🔹 User Query: {user_query}")

    # Remove punctuation for matching
    user_query = user_query.translate(str.maketrans("", "", string.punctuation))

    # Step 1: Check FAQs
    faq_response = fetch_faq_response(user_query)
    if faq_response:
        print(f"✅ FAQ Match Found: {faq_response}")
        return jsonify({"response": faq_response})

    # Step 2: Check Account Information
    account_response = fetch_account_info(user_query)
    if account_response:
        print(f"✅ Account Info Found: {account_response}")
        return jsonify({"response": account_response})

    # Step 3: AI Response
    ai_response = fetch_ai_response(user_query, chat_history)
    print(f"💬 AI Response Sent: {ai_response}")
    
    return jsonify({"response": ai_response})

if __name__ == "__main__":
    print("🚀 Flask server running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
