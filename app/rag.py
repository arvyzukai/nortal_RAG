
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

PERSIST_DIRECTORY = "data/chroma_db"

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_qa_chain():
    if not os.path.exists(PERSIST_DIRECTORY):
        raise ValueError(f"Vector store not found at {PERSIST_DIRECTORY}. Please run ingestion first.")

    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)
    
    # Simple LCEL pattern
    template = """You are an assistant for question-answering tasks about Nortal.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, say that you don't know.
Keep the answer concise.

Context: {context}

Question: {question}

Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Build the chain using LCEL
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Wrap to also return source docs
    def qa_with_sources(question):
        answer = rag_chain.invoke(question)
        docs = retriever.invoke(question)
        return {"answer": answer, "source_documents": docs}
    
    return qa_with_sources
