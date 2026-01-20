# Architecture & Implementation Notes

## 1. Framework Selection: LangChain

**Reasoning:**
I utilized **LangChain** primarily for its **LCEL (LangChain Expression Language)**, which provides a declarative way to compose the retrieval pipeline.

*   **Composability:** The chain is defined as `retriever | format_docs | prompt | llm | parser`. This makes the data flow explicit and easy to modify.
*   **Integration:** Native support for ChromaDB and OpenAI reduces boilerplate code for vector storage and embedding generation.
*   **Retrieval:** The implementation wraps the chain in a custom `qa_with_sources` function to preserve and return specific source metadata (URL, Source Type) alongside the generated answer.

## 2. Scraping Strategy

The scraper (`app/scraper.py`) is designed to handle the specific constraints of modern web architecture (client-side rendering) and diverse content formats (HTML & PDF).

### Core Logic
*   **Selenium:** Used to render JavaScript-heavy components on `nortal.com`. Standard `requests` or `BeautifulSoup` alone would miss content loaded dynamically via React/Angular.
*   **Breadth-First Search (BFS):** Implemented using `collections.deque`. We track URL depth to ensure we capture high-level pages (Services, About) before diving into deep blog posts.
*   **Queue Management:** Stores `(url, depth)` tuples.
*   **Rate Limiting:** A hardcoded `time.sleep(2)` helps prevent blocking.

### Content Processing
*   **Navigation & Noise Removal:** `BeautifulSoup` is configured to strip `<nav>`, `<header>`, `<footer>`, and `<script>` tags. We also target specific class names (e.g., cookie banners) using regex.
*   **PDF Support:** The scraper detects calls to `.pdf` resources. It uses **PyMuPDF (fitz)** to download and extract text from these binary files, treating them as first-class citizens in the indexing pipeline.

## 3. Vector Database & Embeddings

### ChromaDB
*   **Deployment:** Configured in persistent mode (`persist_directory="data/chroma_db"`). This allows the database to run locally without a separate Docker container for the DB itself, simplifying the architecture for this assignment.
*   **Indexing:** We use `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=200) to maintain context across boundaries.

### OpenAI Embeddings
*   **Model:** `text-embedding-3-small`.
*   **Choice:** Selected for its high performance-to-cost ratio and native compatibility with the `GPT-4o` model used for generation.

## 4. API Layer: FastAPI

**Reasoning:**
While Streamlit handles the UI, **FastAPI** provides a robust backend service.

*   **Asynchronous:** The `async def chat(...)` endpoint allows the server to handle concurrent requests without blocking on I/O operations (like OpenAI API calls).
*   **Validation:** **Pydantic** models (`QuestionRequest`, `ChatResponse`) strictly define the API contract, ensuring that clients receive well-structured JSON with typed fields for answers and citations.
