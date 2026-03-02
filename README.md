# 🕵️ Research Agent Pro

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-Vertex_AI-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Status](https://img.shields.io/badge/Status-Operational-success?style=for-the-badge)

**An autonomous AI research assistant capable of searching the live web, reading multiple sources, and synthesizing comprehensive answers.**

---

## 📸 Demo
*(Place your screenshot here, e.g., `![App Screenshot](image_2402e9.png)`)*

## 📖 Overview
**Research Agent Pro** leverages **Google's Gemini 2.5 Flash** model via the **Vertex AI Reasoning Engine**. 

Unlike standard chatbots that rely solely on training data, this agent is equipped with a custom tool belt that allows it to:
1.  **Search** the web in real-time.
2.  **Read** multiple sources.
3.  **Synthesize** facts into a clear summary.

> **Example Query:** *"What are the top rated movies of 2024?"*

---

## 🛠️ Technology Stack

| Component | Tech Used | Why we chose it |
| :--- | :--- | :--- |
| **The Brain** | **Vertex AI (Gemini 2.5)** | Low latency & high reasoning capability. It autonomously decides *when* to search. |
| **The Tools** | **Google Custom Search** | Enterprise-grade reliability. Unlike DuckDuckGo, it provides authenticated access that **doesn't get blocked** by cloud firewalls. |
| **Frontend** | **Streamlit** | Rapid UI development in pure Python. Decouples the frontend from the logic for a clean architecture. |
| ** Hosting** | **Google Cloud Platform** | Serverless deployment ensures the agent is always available without using local resources. |

---

## 🚀 Installation & Setup

### 1. Prerequisites
Create a `.env` file in the root directory with your secrets:
```ini
PROJECT_ID="your-google-project-id"
BUCKET_NAME="your-staging-bucket"
GOOGLE_API_KEY="AIzaSy..."
GOOGLE_CSE_ID="012345..."

2. Install Dependencies
Bash
pip install -r requirements.txt
3. One-Time Backend Setup (Deploy Agent)
Run this only once to upload the brain to the cloud.

Bash
python deploy_research.py
⚠️ Important: After deployment, copy the ReasoningEngine resource ID (starts with projects/...) from the terminal and update it in app.py.

🎮 How to Run
Once installed, you can launch the interface anytime:

PowerShell
# 1. Activate your virtual environment
.\.venv\Scripts\activate

# 2. Launch the web app
streamlit run app.py
📂 Project Structure
research-agent/
├── app.py                 # 🎨 Frontend (Streamlit)
├── deploy_research.py     # 🧠 Backend (Vertex AI Agent)
├── requirements.txt       # 📦 Dependencies
└── .env                   # 🔐 Secrets (Excluded from Git)