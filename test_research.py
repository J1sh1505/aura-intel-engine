import os
from dotenv import load_dotenv

load_dotenv()
# Fallback to None or a default if the env var isn't found
AGENT_ID = os.getenv("VERTEX_AGENT_ID")

# Define a query that requires external knowledge (Google Search)
PROMPT = "What are the key new features in the Google Gemini 1.5 Pro update? Please summarize them in bullet points."

try:
    print(f"Researching: {PROMPT} ...")
    print("(This might take a few seconds as it reads websites)")
    
    # Initialize the remote agent and execute the query
    agent = reasoning_engines.ReasoningEngine(AGENT_ID)
    response = agent.query(prompt=PROMPT)
    
    # Output the synthesized results
    print("\n--- Research Report ---")
    print(response)
    print("-----------------------")
    
except Exception as e:
    print(f"Error: {e}")