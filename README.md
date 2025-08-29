# Smart Contract Vulnerability Analyzer with LLM Orchestration
An advanced, multi-phase vulnerability analysis tool for Solidity smart contracts, powered by a dual-LLM orchestration engine (OpenAI GPT-4o-mini & Google Gemini-1.5-flash) and a simple, interactive frontend built with Streamlit.

This project demonstrates a sophisticated multi-agent approach where two LLMs independently analyze a contract, cross-verify each other's findings with context from a RAG store, and reach a final consensus to produce a detailed and reliable security report

---

## Features

- Dual-LLM Analysis: Leverages the unique strengths of both OpenAI's GPT-4o-mini and Google's Gemini 1.5 Pro for comprehensive vulnerability detection.
- Multi-Phase Orchestration: A sophisticated pipeline that moves from independent analysis to cross-verification and final consensus.
- RAG-Powered Context: Uses a Retriever to provide relevant contract snippets as context during the cross-verification phase, improving accuracy.
- User-Friendly Web UI: An interactive Streamlit frontend for easy contract upload, real-time analysis progress, and clear visualization of results.
- Detailed & Structured Reports: Generates a final JSON report with confirmed/disputed vulnerabilities, including error types, confidence scores, code snippets, rationale, and recommended fixes.

---
## 🛠 Tech Stack

| Layer / Component                 | Technology / Tool                     | Description |
|----------------------------------|--------------------------------------|-------------|
| Frontend                          | Streamlit                             | Interactive web interface for file upload, live phase updates, and report visualization. |
| Backend Orchestration             | Python                                | Coordinates multi-phase analysis of smart contracts. |
| Vulnerability Analysis (Mock)     | MockAnalyzer, DummyRetriever          | Simulates LLM-based analysis and retrieval of relevant contract snippets. |
| LLM Interaction                   | MockLLM                               | Simulates LLM1 and LLM2 for vulnerability detection, verification, and consensus. |
| Data Storage / Reports            | JSON / Local filesystem (`outputs/`)  | Saves phase-wise results and final consolidated report. |
| Contract Language                 | Solidity                              | Smart contracts to be analyzed. |
| Utilities / Helpers               | Python utils                          | Functions for JSON handling, report generation, and prompt management. |
| Environment / Dependency Management | Python 3.8+, pip / Anaconda          | Python environment and package management. |

---
## 📂 Project Structure
```bash
LLM_Vulnerability_Analyser/
├── frontend.py              # Main Streamlit application entry point
├── orchestrator.py          # Main backend logic coordinating the analysis phases
├── llm1_api.py              # Client for OpenAI (GPT) API
├── llm2_api.py              # Client for Google (Gemini) API
├── rag_store.py             # RAG logic for indexing and retrieval
├── utils.py                 # Utility functions for loading prompts and saving JSON
├── prompt_templates/
│   ├── phase1.txt           # Prompt for initial vulnerability analysis
│   ├── phase2.txt           # Prompt for cross-verification with RAG
│   └── phase3.txt           # Prompt for final confirm/dispute consensus
├── outputs/                 # Directory for generated reports (ignored by Git)
├── uploads/                 # Directory for uploaded contracts (ignored by Git)
├── requirements.txt         # Python dependencies
├── .env                     # File for API keys (ignored by Git)
└── .gitignore               # Specifies files and folders for Git to ignore
```
---
## 🚀 Installation
### 🔧 Prerequisites
- Python 3.9+
- pip(Python Package Manager)
- Virtual Environment tool like venv(Optional)
---
### 🧩 Setup Instructions
1. Clone the repository
```bash
git clone https://github.com/a-nushkasharma/Analyzer.git
cd llm_smart_contract_analyzer
```
2. Create virtual environment (optional)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies
- Requirements are mentioned in requirements.txt
```bash
pip install -r requirements.txt
```
4. Set API Keys
- Create a .env file in the root directory:
 ```bash
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
```
- environment variables are already loaded in the codes with
  ```bash
  from dotenv import load_dotenv
  load_dotenv()
  ```
5. Run the app
```bash
streamlit run app.py

# 1.Upload your Solidity smart contract.
# 2.Click "Analyze".
# 3.Download the final JSON vulnerability report.
```
---
## Usage
1. Upload your Solidity smart contract.
2. Click the "Run Vulnerability Analysis" button.
3. Inspect detected vulnerabilities in expandable panels.
4. Download the consolidated JSON report for further processing.
---
## Acknowledgements
Inspired by Large Language Model applications in smart contract analysis.
Mock LLM orchestration and RAG-based verification inspired by research on symbolic and LLM-driven vulnerability detection.
