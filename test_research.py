import requests

# 1. Point this directly to your live cloud AI
URL = "https://aura-intel-engine.onrender.com/research"

# 2. The data we are sending (Matches what Supabase will eventually send)
# NOTE: To see this test show up in your actual React chat, 
# replace "test-group-id-123" with a real group ID from your Supabase table!
payload = {
    "topic": "Artificial Intelligence Startups",
    "group_id": "test-group-id-123" 
}

print(f"🚀 Sending trigger to Render API: {URL}")
print(f"📦 Payload: {payload}")
print("⏳ Waiting for the AI to format the news...")

try:
    # 3. Send the POST request to Render
    response = requests.post(URL, json=payload)
    
    # 4. Print the result
    print(f"\n✅ Status Code: {response.status_code}")
    print("📝 Response from Render:")
    print(response.json())
    
except Exception as e:
    print(f"\n❌ Error connecting to Render: {e}")