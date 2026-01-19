
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

## 📋 Assignment Questions & Architectural Justifications

### 1. Framework Choice: Why LangChain?

I chose **LangChain** over LlamaIndex because:
- **Simplicity for RAG**: LangChain provides a straightforward, composable approach using LCEL (LangChain Expression Language) for building retrieval pipelines.
- **Flexibility**: Easier to customize retrieval logic, integrate custom prompts, and swap components (e.g., vector stores, LLMs).
- **Ecosystem**: Seamless integration with ChromaDB, OpenAI, and Streamlit.
- **Production-Ready**: Battle-tested in production environments with extensive community support.

**Implementation Details:**
- Used LCEL to build a retrieval chain that combines document retrieval with GPT-4o for answer generation.
- Custom `format_docs` function ensures retrieved context is properly formatted for the LLM.
- Wrapped the chain in `qa_with_sources()` to return both answers and source citations.

### 2. Scraping Logic: How does BFS handle rate limiting and deep-nesting?

**Selenium with BFS Implementation:**
- **Why Selenium?** Nortal.com is a modern, JavaScript-heavy site. Selenium renders the page fully, ensuring we capture dynamically loaded content that static scrapers might miss.
- **BFS Queue:** Implements breadth-first traversal using `collections.deque`. Each URL is paired with its depth level `(url, depth)`.
- **Rate Limiting:** Simple `time.sleep(2)` between requests to avoid overwhelming the server. In production, this could use exponential backoff or respect `robots.txt`.
- **Depth Control:** `max_depth=2` parameter limits how deep we crawl. This prevents infinite loops and focuses on high-value pages.
- **Content Cleaning:** Custom `extract_content()` function removes:
  - Navigation, headers, footers, and forms
  - Cookie banners and popups (via regex on class names)
  - JavaScript and style tags
  
This ensures the vector DB only indexes meaningful content, not boilerplate HTML.

### 3. Vector Ops: Why ChromaDB and OpenAI Embeddings?

**ChromaDB:**
- **Local-First Design:** Runs embedded or as a lightweight server - perfect for "local RAG" requirement.
- **Persistence:** Simple directory-based persistence (`data/chroma_db`) - no complex DB setup.
- **Performance:** Fast similarity search with HNSW indexing.

**OpenAI Embeddings (`text-embedding-3-small`):**
- **Quality:** State-of-the-art semantic understanding for retrieval tasks.
- **Consistency:** Same ecosystem as our LLM (GPT-4o), ensuring embedding-generation alignment.
- **Cost-Effective:** Affordable for moderate-scale indexing.

### 4. API Layer: Why FastAPI?

- **Performance:** Asynchronous support allows handling multiple requests efficiently.
- **Validation**: Pydantic models ensure data integrity for requests and responses.
- **Documentation**: Automatic OpenAPI (Swagger) documentation available at `/docs`.
- **Integration**: Easily consumed by any frontend or external service, moving beyond manual Streamlit interactions.

---

## 🛠 Tech Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **Web Scraping** | Selenium + BeautifulSoup | Handles JavaScript-heavy sites, extracts clean text |
| **RAG Framework** | LangChain (LCEL) | Composable, flexible, production-ready |
| **Vector Store** | ChromaDB | Local, persistent, easy setup |
| **Embeddings** | OpenAI Embeddings | High quality, consistent with LLM |
| **LLM** | GPT-4o | Latest OpenAI model, strong reasoning |
| **Backend API** | FastAPI + Uvicorn | High-performance, asynchronous, typed API |
| **Frontend** | Streamlit | Rapid prototyping, built-in chat UI |
| **Orchestration** | Docker Compose | Multi-service orchestration (UI, API, Selenium) |

---

## 📂 Project Structure

```
nortal_rag/
├── app/
│   ├── __init__.py         # Package marker
│   ├── api.py              # FastAPI backend endpoints
│   ├── ingest.py           # Vector DB indexing
│   ├── main.py             # Streamlit UI
│   ├── rag.py              # LangChain retrieval chain
│   └── scraper.py          # Selenium scraper with BFS
├── data/
│   ├── chroma_db/          # Vector store persistence
│   └── scraped_data.json   # Scraped content cache
├── tests/                  # API and RAG integration tests (pytest)
│   ├── test_api.py         # FastAPI endpoint tests
│   └── test_rag.py         # RAG pipeline integration tests
├── .env.example            # Environment template
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

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

---

## 📊 Sample Queries

- *"What services does Nortal provide?"*
- *"Tell me about Nortal's 25-year anniversary."*
- *"Where are Nortal's offices located?"*
- *"What is Nortal's experience with digital government?"*

---

## 🎯 Code Ownership & Understanding

All code in this repository was written with full understanding:
- **Scraper:** Custom BFS implementation with depth control and content cleaning.
- **RAG Pipeline:** LCEL-based chain composition, avoiding deprecated `RetrievalQA`.
- **Deployment:** Multi-service Docker Compose with Selenium standalone container.

Key design decisions were made to prioritize **simplicity**, **maintainability**, and **AI engineering best practices**.

---

## 🔧 Configuration

### Scraper Parameters (in `app/scraper.py`)
```python
max_pages=10    # Total pages to scrape
max_depth=2     # BFS depth limit
```

### RAG Parameters (in `app/rag.py`)
```python
search_kwargs={"k": 3}  # Number of documents to retrieve
temperature=0           # Deterministic responses
```

---

## 📝 Future Enhancements

- **Async Scraping:** Use `aiohttp` + async Selenium for faster crawling.
- **Incremental Updates:** Detect changed pages and re-index only deltas.
- **Production DB:** Migrate to Weaviate or Pinecone for scale.
- **Auth & Multi-Tenancy:** Add user authentication and isolated vector stores.
- **Evaluation:** Implement RAG evaluation metrics (faithfulness, relevance).

---

## 📄 License

This project is a technical assignment demonstration.

---

## 👤 Author

Created as part of Nortal's technical assessment. Demonstrates expertise in:
- AI Engineering (RAG, LangChain, Vector DBs)
- Web Scraping (Selenium, BeautifulSoup)
- Full-Stack Development (Python, Streamlit, Docker)

