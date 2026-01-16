
from app.rag import get_qa_chain

try:
    qa_func = get_qa_chain()
    query = "What is Nortal's 25th anniversary message?"
    print(f"Query: {query}")
    result = qa_func(query)
    print("\nAnswer:")
    print(result['answer'])
    print("\nSources:")
    for doc in result['source_documents']:
        print(f"- {doc.metadata.get('title', 'No Title')}: {doc.metadata.get('source', 'No URL')}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
