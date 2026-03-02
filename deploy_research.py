import os
import vertexai
from dotenv import load_dotenv
from exa_py import Exa
from vertexai.preview import reasoning_engines
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration

load_dotenv()
vertexai.init(project=os.getenv("PROJECT_ID"), location="us-central1", staging_bucket=f"gs://{os.getenv('BUCKET_NAME')}")
MY_EXA_KEY = os.getenv("EXA_API_KEY")

def exa_research_tool(query: str):
    """Searches Exa.ai and returns formatted summaries."""
    try:
        res = Exa(api_key=MY_EXA_KEY).search_and_contents(query, type="neural", num_results=3, text=True)
        return "\n\n".join([f"Title: {r.title}\nURL: {r.url}\nSummary: {r.text[:1000]}..." for r in res.results])
    except Exception as e: return f"Search Error: {e}"

search_tool = Tool(function_declarations=[FunctionDeclaration(
    name="exa_research_tool", description="Neural web search for answers/news.",
    parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
)])

class ResearchAgent:
    def __init__(self):
        self.model = GenerativeModel("gemini-2.5-flash", tools=[search_tool])

    def query(self, prompt: str):
        resp = self.model.generate_content(prompt)
        try:
            if resp.candidates[0].function_calls:
                call = resp.candidates[0].function_calls[0]
                print(f"DEBUG: Researching '{call.args['query']}'...")
                data = exa_research_tool(call.args['query'])
                return self.model.generate_content(f"Question: {prompt}\nData: {data}\nSynthesize answer.").text
        except Exception: pass
        return resp.text

print("Deploying...")
remote_agent = reasoning_engines.ReasoningEngine.create(
    ResearchAgent(),
    requirements=["google-cloud-aiplatform", "python-dotenv", "exa-py"],
    display_name="Exa Research Agent",
)
print(f"Deployed! ID: {remote_agent.resource_name}")