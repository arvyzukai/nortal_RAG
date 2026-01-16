
import json
import os
import shutil
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

PERSIST_DIRECTORY = "data/chroma_db"

def ingest_data(json_path="data/scraped_data.json"):
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found. Run scraper first.")
        return

    # Load data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    for entry in data:
        # Create a document for each page
        # Metadata is crucial for citations
        doc = Document(
            page_content=entry.get("content", ""),
            metadata={"source": entry.get("url", ""), "title": entry.get("title", "")}
        )
        documents.append(doc)

    # Split text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")

    # Create Embeddings
    embeddings = OpenAIEmbeddings()

    # Clear existing DB if needed (optional, for clean re-runs)
    # if os.path.exists(PERSIST_DIRECTORY):
    #     shutil.rmtree(PERSIST_DIRECTORY)

    # Store in Chroma
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )
    print(f"Ingestion complete. Vector store saved to {PERSIST_DIRECTORY}")

if __name__ == "__main__":
    ingest_data()
