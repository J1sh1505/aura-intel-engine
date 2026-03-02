from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from supabase import create_client, Client
from tavily import TavilyClient
import os
import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

# --- Initialize Supabase & Tavily ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# --- 1. The Actual News Fetching Logic ---
def fetch_hourly_news():
    print(f"[{datetime.datetime.now()}] Running Automated Pulse...")
    try:
        # 1. Find active groups
        res = supabase.table("groups").select("*").eq("bot_active", True).execute()
        active_groups = res.data
        
        for group in active_groups:
            name = group.get('name')
            group_id = group.get('id')
            
            # 2. Search for news
            search_res = tavily.search(query=f"Breaking news for {name} industry", search_depth="advanced", max_results=2)
            
            for article in search_res['results']:
                # 3. Post to the actual messages table!
                supabase.table("group_messages").insert({
                    "group_id": group_id,  # Critical for React to link it!
                    "content": f"**AI Update:** {article['title']}\n\n{article['content']}",
                    "is_bot": True, # Or whatever your boolean is
                    "created_at": datetime.datetime.now().isoformat()
                }).execute()
                
        print("✅ Automated Pulse Completed!")
    except Exception as e:
        print(f"❌ Background Task Error: {e}")

# --- 2. Set up the Scheduler ---
scheduler = BackgroundScheduler()
# Set to 'cron', hour=9 if you want exactly 9 AM, or keep 'interval', hours=1
scheduler.add_job(fetch_hourly_news, 'interval', hours=1) 
scheduler.start()

# 3. Add a Lifespan to handle shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# 1. Load Environment Variables
load_dotenv()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

# 2. Setup FastAPI
app = FastAPI(title="Deep Research Agent API")

# 3. Setup CORS (Crucial: Allows your React website to talk to this Python server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Define the Request Model (What the frontend sends us)
class SearchRequest(BaseModel):
    query: str

# 5. The Search Endpoint
@app.post("/api/research")  # We'll use this URL in React
async def search_agent(request: SearchRequest):
    print(f"📥 Received query: {request.query}")

    if not PROJECT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLOUD_PROJECT not set in .env")

    try:
        # --- AGENT LOGIC ---
        
        # A. Setup Client
        client = genai.Client(
            vertexai=True, 
            project=PROJECT_ID, 
            location="us-central1"
        )

        # B. Define Google Search Tool
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        # C. The "Nuclear" Prompt (Same one that worked perfectly in Streamlit)
        today = datetime.date.today().strftime("%B %d, %Y")
        prompt = f"""
        You are a Research Engine. 
        CURRENT DATE: {today}
        QUERY: {request.query}
        
        INSTRUCTIONS: 
        1. Search Google for the latest live data. 
        2. Ignore any future predictions (like 2026/2027) unless explicitly labeled as "forecast".
        3. DO NOT chat. DO NOT say "Okay". Just output the report.

        --- BEGIN REPORT ---
        
        # Executive Summary
        (Provide a 200-word data-driven summary. Bold key metrics.)

        # Strategic Analysis
        (Use h3 headers and bullet points.)

        # Financials & Data
        (You MUST output a Markdown table. If data is missing, write "N/A".)
        
        | Metric | Value | Source |
        | :--- | :--- | :--- |
        | (e.g. Revenue) | (e.g. $10M) | (e.g. TechCrunch) |

        # Strategic Outlook
        (Short term vs Long term)\

        # Sources
        (List URLs)
        """

        # D. Run Generation
        print("Searching Google & Synthesizing Report...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"]
            )
        )

        # E. Process Response
        if response.candidates and response.candidates[0].content.parts:
            report_text = response.candidates[0].content.parts[0].text
            
            # Extract Sources (for the frontend to display nicely if needed)
            sources = []
            try:
                for candidate in response.candidates:
                    if candidate.grounding_metadata.grounding_chunks:
                        for chunk in candidate.grounding_metadata.grounding_chunks:
                            if chunk.web:
                                sources.append({"title": chunk.web.title, "url": chunk.web.uri})
            except:
                pass

            # Return Clean JSON
            return {
                "content": report_text,
                "sources": sources
            }
        else:
            raise HTTPException(status_code=500, detail="No response from Gemini.")

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Run on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)