
import streamlit as st
import os
from rag import get_qa_chain

st.set_page_config(page_title="Nortal Intelligence", page_icon="🤖")

st.title("Nortal Intelligence 🤖")
st.markdown("Ask questions about Nortal's services, expertise, and global presence.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "qa_func" not in st.session_state:
    try:
        st.session_state.qa_func = get_qa_chain()
    except Exception as e:
        st.error(f"Failed to initialize RAG pipeline: {e}. Make sure data is ingested.")
        st.session_state.qa_func = None

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What would you like to know?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    if st.session_state.qa_func:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.qa_func(prompt)
                    answer = result['answer']
                    source_docs = result['source_documents']
                    
                    st.markdown(answer)
                    
                    # Display sources in an expander
                    with st.expander("View Sources"):
                        for i, doc in enumerate(source_docs):
                            st.markdown(f"**Source {i+1}**: [{doc.metadata.get('title', 'Link')}]({doc.metadata.get('source', '#')})")
                            st.text(doc.page_content[:200] + "...")
                            
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error generating response: {e}")
    else:
        st.error("RAG pipeline is not ready. Please check if data is ingested.")
