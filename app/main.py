
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
# Set LangSmith project for Streamlit
os.environ["LANGCHAIN_PROJECT"] = "nortal-rag-streamlit"

from rag import get_qa_chain
from scraper import NortalScraper
from ingest import ingest_data

st.set_page_config(page_title="Nortal Intelligence", page_icon="🤖")

st.title("Nortal Intelligence 🤖")
st.markdown("Ask questions about Nortal's services, expertise, and global presence.")

# Check if data exists, if not offer to initialize
if not os.path.exists("data/chroma_db"):
    st.warning("⚠️ Vector database not initialized. The app needs data to answer questions.")
    
    # Check if we have pre-existing data
    has_local_data = os.path.exists("data/scraped_data.json")
    
    if has_local_data:
        st.info("📂 Found 'scraped_data.json' locally. You can initialize the database using this existing data.")
        if st.button("🚀 Initialize from Existing Data (Fast)"):
            with st.spinner("Building vector database from 'scraped_data.json'..."):
                try:
                    ingest_data()
                    st.success("✅ Database initialized from local data!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Ingestion failed: {e}")
                    st.stop()
    
    st.markdown("---")
    st.markdown("### Or start from scratch")
    st.markdown("If you want fresh data, you can scrape the website again.")
    
    st.markdown("""
    **Setup Steps:**
    1. Scrape nortal.com (takes ~15 seconds for 3 pages)
    2. Create embeddings and build the vector database (takes ~10 seconds)
    
    **Note:** You need to set your `OPENAI_API_KEY` in Streamlit Secrets for this to work.
    """)
    
    if st.button("🔄 Scrape & Initialize (Full Setup)"):
        with st.spinner("Step 1/2: Scraping nortal.com..."):
            try:
                # Use robust scraping settings
                scraper = NortalScraper(max_pages=3, max_depth=1)
                scraper.scrape()
                st.success("✅ Scraping complete!")
            except Exception as e:
                st.error(f"Scraping failed: {e}")
                st.stop()
        
        with st.spinner("Step 2/2: Building vector database..."):
            try:
                ingest_data()
                st.success("✅ Database initialized!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Ingestion failed: {e}")
                st.stop()
    
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "qa_func" not in st.session_state:
    try:
        st.session_state.qa_func = get_qa_chain()
    except Exception as e:
        st.error(f"Failed to initialize RAG pipeline: {e}")
        st.info("Try reinitializing the database using the button above.")
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
        st.error("RAG pipeline is not ready. Please reinitialize the database.")
