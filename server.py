from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from supabase import create_client, Client
import os
import datetime
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Setup FastAPI
app = FastAPI(title="AI Daily News Anchor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Request Model
class NewsTriggerRequest(BaseModel):
    topic: str
    group_id: str

# 4. The Single, Focused News Endpoint
@app.post("/research")
async def generate_news_feed(request: NewsTriggerRequest):
    print(f"📥 Received News Trigger for topic: {request.topic} | Group: {request.group_id}")

    if not PROJECT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLOUD_PROJECT not set in .env")

    try:
        # A. Setup Gemini Client 
        # (Vertex AI automatically uses /etc/secrets/gcp_keys.json via the GOOGLE_APPLICATION_CREDENTIALS env var)
        client = genai.Client(
            vertexai=True, 
            project=PROJECT_ID, 
            location="us-central1"
        )
        
        google_search_tool = types.Tool(google_search=types.GoogleSearch())

        # B. The Ultra-Strict "Card-Only" Prompt
        # This prompt is designed to kill all conversational filler that triggers standard chat bubbles.
        today = datetime.date.today().strftime("%B %d, %Y")
        prompt = f"""
        ACT AS: The AUTOMATED COMMUNITY INTEL engine.
        CURRENT DATE: {today}
        TOPIC: {request.topic}
        
        CRITICAL RULES:
        1. NO CONVERSATION. Do not say "Okay," "I will," or "Here is." 
        2. NO INTRODUCTIONS. Start the response immediately with the rocket symbol.
        3. FORMAT: You must use the exact Markdown below to trigger the Big Box UI.

        🚀 **INTELLIGENCE UPDATE: {request.topic.upper()}**
        
        [Brief summary of today's status regarding {request.topic}]

        ### [Breaking News Headline 1]
        [3 sentences of news summary]

        ### [Breaking News Headline 2]
        [3 sentences of news summary]
        
        🔗 **Source:** [Insert one valid URL here]
        """

        # C. Generate the News
        print("🔍 Searching Google & Formatting News Box...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
                temperature=0.2  # Lower temperature for maximum instruction following
            )
        )

        if response.candidates and response.candidates[0].content.parts:
            news_content = response.candidates[0].content.parts[0].text
            
            # D. Insert directly into the Supabase Chat
            # We use is_ai_intel: True to bypass standard chat and hit the 'Intelligence' section.
            print(f"💾 Saving news to group {request.group_id}...")
            supabase.table("group_messages").insert({
                "group_id": request.group_id,
                "content": news_content,
                "is_ai_intel": True, 
                "created_at": datetime.datetime.now().isoformat()
            }).execute()

            return {"status": "success", "message": "News posted to chat", "content": news_content}
        else:
            raise HTTPException(status_code=500, detail="No response from Gemini.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Local port 8000; Render will override this dynamically.
    uvicorn.run(app, host="0.0.0.0", port=8000)