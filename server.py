from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from supabase import create_client, Client
import os
import json
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

# 3. Request Model (Matches what your Supabase Bridge sends)
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
        # A. Setup Gemini Client with Authentication (The Bulletproof Method)
        google_json_string = os.getenv("GOOGLE_CREDENTIALS_JSON")
        
        if google_json_string:
            print("🔐 Creating temporary Google Cloud credential file...")
            # 1. Write the JSON string from Render into a temporary file
            key_path = "/tmp/gcp_keys.json"
            with open(key_path, "w") as f:
                f.write(google_json_string)
            
            # 2. Tell Google's internal systems exactly where this file is
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
            
            # 3. Now initialize the client normally; Google will find the file automatically!
            client = genai.Client(
                vertexai=True, 
                project=PROJECT_ID, 
                location="us-central1"
            )
        else:
            print("🖥️ Running locally: Using default Google Cloud credentials...")
            client = genai.Client(
                vertexai=True, 
                project=PROJECT_ID, 
                location="us-central1"
            )

        google_search_tool = types.Tool(google_search=types.GoogleSearch())

        # B. The Strict "News Reporter" Prompt
        today = datetime.date.today().strftime("%B %d, %Y")
        prompt = f"""
        You are an AI Daily News Anchor.
        CURRENT DATE: {today}
        TOPIC TO COVER: {request.topic}
        
        INSTRUCTIONS: 
        1. Search Google for the latest breaking news regarding the TOPIC.
        2. Select the top 1 or 2 most important recent news stories.
        3. DO NOT output conversational text, strategic analysis, or standard bullet points.
        4. Format EACH story exactly like the template below using Markdown blockquotes (>) to create a 'Big Box' effect.

        REQUIRED TEMPLATE:
        > **[Headline of the Article]**
        > [A concise, 2-3 sentence engaging summary of the article]
        > 
        > **URL:** [Insert actual link to the article]
        > **Credit:** [Author Name or "Unknown Author"]
        """

        # C. Generate the News
        print("🔍 Searching Google & Formatting News Box...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
                temperature=0.3 # Lower temperature keeps formatting strict
            )
        )

        if response.candidates and response.candidates[0].content.parts:
            news_content = response.candidates[0].content.parts[0].text
            
            # D. Insert directly into the Supabase Chat!
            print(f"💾 Saving news to group {request.group_id}...")
            supabase.table("group_messages").insert({
                "group_id": request.group_id,
                "content": news_content,
                "is_bot": True,
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
    uvicorn.run(app, host="0.0.0.0", port=8000)