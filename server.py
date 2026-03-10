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
    print(f"Received News Trigger for topic: {request.topic} | Group: {request.group_id}")

    if not PROJECT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLOUD_PROJECT not set in .env")

    try:
        # A. Setup Gemini Client 
        client = genai.Client(
            vertexai=True, 
            project=PROJECT_ID, 
            location="us-central1"
        )
        
        google_search_tool = types.Tool(google_search=types.GoogleSearch())

        # B. Updated Consolidated Prompt
        # Rule 4 & 5 specifically address the single-block format and author credit.
        today = datetime.date.today().strftime("%B %d, %Y")
        prompt = f"""
        ACT AS: The AUTOMATED COMMUNITY INTEL engine.
        CURRENT DATE: {today}
        TOPIC: {request.topic}
        
        CRITICAL RULES:
        1. NO CONVERSATION. Do not say "Okay," "I will," or "Here is." 
        2. NO INTRODUCTIONS. Start the response immediately with the rocket symbol.
        3. SINGLE BLOCK ONLY: Do not split news into multiple messages. Everything must be in ONE Markdown string.
        4. AUTHOR CREDIT: You must identify the author or publication of the news.
        5. FORMAT: You must use the exact Markdown below to trigger the Big Box UI:

        **INTELLIGENCE UPDATE: {request.topic.upper()}**
        
        [Overall summary of today's status regarding {request.topic}]

        ### [Breaking News Headline 1]
        [3 sentences of news summary]
        **Source:** [Insert URL]
        **Author/Credit:** [Insert Name of Author or Publication]

        ---

        ### [Breaking News Headline 2]
        [3 sentences of news summary]
        **Source:** [Insert URL]
        **Author/Credit:** [Insert Name of Author or Publication]
        """

        # C. Generate the News
        print("Searching Google & Formatting News Box...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
                temperature=0.2 
            )
        )

        if response.candidates and response.candidates[0].content.parts:
            news_content = response.candidates[0].content.parts[0].text
            
            # D. The "Shotgun" approach - send all possible flags to overcome UI routing issues
            supabase.table("group_messages").insert({
                "group_id": request.group_id,
                "content": news_content,
                "is_ai_intel": True,  # Standard flag [cite: 24, 35]
                "is_bot": True,       # Backup flag 1 [cite: 26, 34]
                "is_intel": True,     # Backup flag 2 [cite: 28]
                "created_at": datetime.datetime.now().isoformat()
            }).execute()

            return {"status": "success", "message": "News posted to chat", "content": news_content}
        else:
            raise HTTPException(status_code=500, detail="No response from Gemini.")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)