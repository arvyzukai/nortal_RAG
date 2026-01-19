import pytest
from app.rag import get_qa_chain

def test_rag_query():
    """Test the RAG pipeline with a specific query."""
    try:
        qa_func = get_qa_chain()
        query = "What is Nortal's 25th anniversary message?"
        result = qa_func(query)
        
        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0
        
        assert "source_documents" in result
        assert len(result["source_documents"]) > 0
        
        print(f"\nRAG test passed! Answer: {result['answer'][:100]}...")
    except ValueError as e:
        pytest.fail(f"Vector store not found: {e}")
    except Exception as e:
        pytest.fail(f"RAG test failed with error: {e}")

if __name__ == "__main__":
    test_rag_query()
