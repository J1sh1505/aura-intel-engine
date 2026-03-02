import streamlit as st
from google import genai
from google.genai import types
from tavily import TavilyClient
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from supabase import create_client, Client
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

# --- 1. CONFIG & DB CONNECTION ---
st.set_page_config(page_title="Agentic Intel Hub", page_icon="⚡", layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily = TavilyClient(api_key=TAVILY_API_KEY)

# --- 2. RESEARCH TEMPLATE ENGINE ---
def generate_structured_research(query, project_id):
    """Generates the high-end Manual Search template with specific sections."""
    client = genai.Client(vertexai=True, project=project_id, location="us-central1")
    
    prompt = f"""
    Perform deep, professional research on: {query}
    
    Structure your response EXACTLY with these Markdown headers:
    # 📑 EXECUTIVE SUMMARY
    Provide a 3-sentence high-level overview.
    
    # 🔍 DEEP SEARCH ANALYSIS
    Detail the key findings, data points, and market trends.
    
    # 🛠️ IMPLEMENTATION GUIDE
    Provide actionable, step-by-step advice based on the findings.
    
    # 🔗 SOURCES & INTEL
    List the key entities, companies, or URLs found during research.
    """
    
    resp = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )
    return resp.text

# --- 3. AUTOMATION LOGIC (The 9 AM Pulse) ---
def run_daily_pulse():
    """Triggered daily at 9am. It fetches group topics and runs AI news pulse."""
    try:
        # 1. Fetch active groups
        res = supabase.table("groups").select("*").execute()
        # Check both boolean possibilities based on your table setup
        active_groups = [g for g in res.data if g.get('bot_active') in [True, 'true', 'TRUE'] or g.get('is_bot_active') in [True, 'true', 'TRUE']]
        
        for group in active_groups:
            group_id = group.get('id')
            creator_id = group.get('created_by') 
            topic = group.get('name', 'General Tech')
            
            # 2. Get the news
            search_res = tavily.search(query=f"Breaking news for {topic}", search_depth="advanced", max_results=1)
            
            if search_res.get('results'):
                news_snippet = search_res['results'][0].get('content', 'No content found.')
                source_url = search_res['results'][0].get('url', '')

                intel_content = f"📡 **INTELLIGENCE UPDATE: {topic.upper()}**\n\n"
                intel_content += f"{news_snippet[:600]}...\n\n"
                if source_url:
                    intel_content += f"🔗 Source: {source_url}"
                
                # 3. INSERT INTO group_messages (matches React frontend)
                msg_data = {
                    "group_id": group_id,
                    "content": intel_content,
                    "sender_id": creator_id, 
                    "is_ai_intel": True,    
                    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                
                # CHANGED TABLE TO group_messages
                insert_result = supabase.table("group_messages").insert(msg_data).execute()
                
                if insert_result.data:
                    print(f"✅ Pulsed news to {topic}")
                else:
                    print(f"⚠️ Insert failed for {topic}: {insert_result}")
            
    except Exception as e:
        print(f"Automation Error: {e}")

# Start Background Scheduler
if "scheduler_started" not in st.session_state:
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_daily_pulse, CronTrigger(hour=9, minute=0))
    scheduler.start()
    st.session_state.scheduler_started = True

# --- 4. UI ---
with st.sidebar:
    st.header("⚙️ Agent Controls")
    g_project_id = st.text_input("GCP Project ID", value="my-first-agent-484718")
    st.divider()
    
    if st.button("🚀 Force 9 AM Pulse Now", use_container_width=True):
        with st.spinner("Pushing news to active groups..."):
            run_daily_pulse()
            st.success("Pulse executed successfully!")

st.title("🛡️ Agentic Intelligence Hub")
tab_search, tab_news = st.tabs(["🔍 Strategic Deep Dive", "🗞️ Community Intel Feed"])

with tab_search:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("Research Parameters")
        topic = st.text_area("Research Topic", placeholder="Analyze competitive trends in UK Fintech...")
        if st.button("Execute Deep Research", type="primary", use_container_width=True):
            if topic and g_project_id:
                with st.status("🧠 Agent is researching..."):
                    result = generate_structured_research(topic, g_project_id)
                    st.session_state.last_research = result
            else:
                st.warning("Project ID and Topic are required.")

    with col_r:
        if "last_research" in st.session_state:
            st.markdown(st.session_state.last_research)
        else:
            st.info("Your structured research report will appear here.")

with tab_news:
    st.subheader("📡 Community Intelligence")
    try:
        response = supabase.table("groups").select("*").execute()
        active_reports = [r for r in response.data if r.get('bot_active') in [True, 'true', 'TRUE'] or r.get('is_bot_active') in [True, 'true', 'TRUE']]
        
        if active_reports:
            for item in active_reports:
                st.markdown(f"""
                <div style="background-color: #1a1c24; padding: 20px; border-radius: 12px; border-left: 5px solid #00ccff; margin-bottom: 20px; border: 1px solid #30363d;">
                    <h4 style="margin:0; color:#00ccff;">{item.get('name').upper()}</h4>
                    <p style="font-size: 0.8rem; color: #888;">STATUS: 🟢 AGENT ACTIVE</p>
                    <p>{item.get('description', 'No description provided.')}</p>
                    <hr style="border: 0.1px solid #30363d;">
                    <small>Agent checking for updates every morning at 9:00 AM.</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No active groups found.")
    except Exception as e:
        st.error(f"Feed Error: {e}")