
# Nortal Intelligence - RAG Platform

A local Retrieval-Augmented Generation (RAG) platform that scrapes `nortal.com`, indexes the content into a vector database, and provides an AI-powered chat interface to answer questions about Nortal's services, expertise, and global presence.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key

### Local Development Setup

1. **Clone the repository:**
   ```bash
   cd nortal_rag
   ```

2. **Create virtual environment (using `uv` recommended):**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   # Edit .env and set OPENAI_API_KEY=sk-...
   ```

4. **Initialize Data (Optional if using included DB):**
   ```bash
   python app/scraper.py
   python app/ingest.py
   ```

5. **Launch Services:**
   - **Frontend (Streamlit):** `streamlit run app/main.py`
   - **Backend (FastAPI):** `uvicorn app.api:app --reload`

---

## 🐳 Docker Deployment

**Run the entire platform (Frontend, API, and Selenium) with a single command:**

```bash
docker-compose up --build
```

**Services included:**
- **Streamlit UI:** [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend:** [http://localhost:8000](http://localhost:8000)
- **Selenium Standalone:** Handles JavaScript rendering for the scraper.

## 🧪 Verification & Testing

### 1. API Health Check
```bash
curl http://localhost:8000/health
```

### 2. Run Automated Tests
All tests are located in the `tests/` directory and use `pytest`.

Ensure the API server is running (`uvicorn app.api:app`), then run:
```bash
# Using the virtual environment
.venv\Scripts\python.exe -m pytest tests/
```

---

## 📋 Architecture

Detailed architectural decisions and implementation notes can be found in [ARCHITECTURE.md](ARCHITECTURE.md).

## 🛠 Tech Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Web Scraping** | Selenium + BeautifulSoup + PyMuPDF | Handles JavaScript-heavy sites & PDF documents |
| **RAG Framework** | LangChain (LCEL) | Composable, flexible, production-ready |
| **Vector Store** | ChromaDB | Local, persistent, easy setup |
| **Embeddings** | OpenAI Embeddings | High quality, consistent with LLM |
| **LLM** | GPT-4o | Latest OpenAI model, strong reasoning |
| **Backend API** | FastAPI + Uvicorn | High-performance, asynchronous, typed API |
| **Frontend** | Streamlit | Rapid prototyping, built-in chat UI |
| **Observability** | LangSmith | Tracing, debugging, and monitoring RAG chains |
| **Orchestration** | Docker Compose | Multi-service orchestration (UI, API, Selenium) |

---

## 🔍 How It Works

1. **Scraping:** `app/scraper.py` visits nortal.com, extracts clean text using BeautifulSoup, and saves to JSON.
2. **Indexing:** `app/ingest.py` splits text into chunks, generates embeddings via OpenAI, and stores in ChromaDB.
3. **Retrieval:** When a user asks a question:
   - The query is embedded
   - Top-3 most similar chunks are retrieved from ChromaDB
   - Retrieved context + query are sent to GPT-4o
   - GPT-4o generates a concise answer
   - Sources are displayed with links
4. **Interfaces:**
   - **Streamlit:** Provides a user-friendly chat interface with message history and source citations.
   - **FastAPI:** Provides a programmatic `/chat` endpoint for integration with other systems.

> [!NOTE]
> The current implementation is a Proof of Concept (POC). It provides **chat history** (context within the current session) but does not have **persistent memory** across different sessions.

---

## 📊 Sample Queries

- *"What services does Nortal provide?"*
- *"Tell me about Nortal's 25-year anniversary."*
- *"Where are Nortal's offices located?"*
- *"What is Nortal's experience with digital government?"*

---

## 📝 Future Enhancements

The development roadmap focuses on iterative improvements driven by experimental data rather than speculative feature additions.

-   **Chat Memory:** Implement persistent conversational memory to allow follow-up questions and context retention across messages.
-   **LangChain Tool Integration:** Experiment with giving the LLM access to specific tools (e.g., calculator, search API) to handle queries that require external computation or real-time data.
-   **Agentic Workflows:** Investigate agentic orchestration to handle complex multi-step reasoning. This includes implementing guardrails for ethical considerations and preventing jailbreaking.
-   **Human Handoff:** additions of a fallback mechanism to route the conversation to a human operator after a configurable number of interactions or if satisfaction metrics drop.
-   **Iterative Optimization:** Continuous refinement of chunking strategies, embedding models, and retrieval parameters based on quantitative evaluation results.

---

## 📄 License

This project is a technical assignment demonstration.

---

## 👤 Author

Created as part of Nortal's technical assessment. Demonstrates expertise in:
- AI Engineering (RAG, LangChain, Vector DBs)
- Web Scraping (Selenium, BeautifulSoup)
- Full-Stack Development (Python, Streamlit, Docker)

