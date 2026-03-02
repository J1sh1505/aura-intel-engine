import vertexai
from vertexai.generative_models import GenerativeModel

# Initialize your project
vertexai.init(project="my-first-agent-484718", location="us-central1")

print("🔍 Checking available models for your project...")

# The list of models we want to test
candidates = [
    "gemini-1.5-flash-002", # Newest Stable Flash
    "gemini-1.5-flash-001", # Older Stable Flash
    "gemini-1.5-pro-002",   # Newest Stable Pro
    "gemini-1.5-pro-001",   # Older Stable Pro
    "gemini-1.0-pro",       # Old Reliable
]

for model_name in candidates:
    try:
        model = GenerativeModel(model_name)
        # We try to generate one token to prove access works
        response = model.generate_content("Test", stream=False)
        print(f"✅ WORKS: {model_name}")
    except Exception as e:
        # If it fails, we know we can't use this one
        print(f"❌ FAILED: {model_name}")

print("\nDone! Use one of the models marked ✅.")