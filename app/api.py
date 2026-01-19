from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.rag import get_qa_chain
import uvicorn
import os

app = FastAPI(title="Nortal RAG API")

# Initialize RAG chain
try:
    qa_func = get_qa_chain()
except Exception as e:
    print(f"Error initializing RAG chain: {e}")
    qa_func = None

class QuestionRequest(BaseModel):
    question: str

class SourceDocument(BaseModel):
    page_content: str
    metadata: dict

class ChatResponse(BaseModel):
    answer: str
    source_documents: List[SourceDocument]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "rag_ready": qa_func is not None}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: QuestionRequest):
    if not qa_func:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    try:
        result = qa_func(request.question)
        
        # Transform LangChain documents to our Pydantic model
        source_docs = [
            SourceDocument(page_content=doc.page_content, metadata=doc.metadata)
            for doc in result['source_documents']
        ]
        
        return ChatResponse(
            answer=result['answer'],
            source_documents=source_docs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
