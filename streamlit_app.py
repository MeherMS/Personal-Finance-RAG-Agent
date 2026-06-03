# streamlit_app.py

import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Import our custom modules
from document_processor import DocumentProcessor
from data_pipeline import DataPipeline
from agent import FinanceAgent

# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="💰 Personal Finance RAG Agent",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
    }
    .chat-message.assistant {
        background-color: #f5f5f5;
        border-left: 4px solid #666;
    }
    .metadata {
        font-size: 0.85rem;
        color: #999;
        margin-top: 0.5rem;
        font-style: italic;
    }
    .source-badge {
        display: inline-block;
        background-color: #e8f4f8;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================

st.sidebar.markdown("# ⚙️ Configuration")

# Data management section
st.sidebar.markdown("### 📂 Data Management")

if st.sidebar.button("🔄 Reset All Data", key="reset_all"):
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# File paths
st.sidebar.markdown("### 📁 File Paths")
synthetic_csv = st.sidebar.text_input(
    "Synthetic CSV:",
    value="synthetic_bank_statement.csv"
)
processed_csv = st.sidebar.text_input(
    "Processed CSV:",
    value="processed_transactions.csv"
)
chroma_path = st.sidebar.text_input(
    "Chroma DB Path:",
    value="./chroma_vectordb"
)

st.sidebar.markdown("---")

# Status section
st.sidebar.markdown("### 🔍 Status")
status_col = st.sidebar.empty()

# ==================== INITIALIZE SESSION STATE ====================

if "agent" not in st.session_state:
    st.session_state.agent = None
    st.session_state.data_loaded = False
    st.session_state.chat_history = []
    st.session_state.processing_complete = False

# ==================== MAIN INTERFACE ====================

# Title
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.markdown('<div class="main-title">💰 Personal Finance RAG Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your Money Therapist - Ask questions about your spending</div>', unsafe_allow_html=True)

# ==================== TABS ====================

tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Data", "ℹ️ About"])

# ==================== TAB 1: CHAT ====================

with tab1:
    st.markdown("### Chat with Your Finance Agent")
    
    # Initialize agent button
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🚀 Initialize Agent", key="init_agent"):
            with st.spinner("Initializing..."):
                try:
                    # Check if data exists
                    if not os.path.exists(chroma_path):
                        st.error(f"❌ Chroma database not found at {chroma_path}")
                        st.info("Run the data pipeline first (see Data tab)")
                    else:
                        st.session_state.agent = FinanceAgent(chroma_db_path=chroma_path)
                        st.session_state.data_loaded = True
                        st.success("✅ Agent initialized!")
                        status_col.success("✅ Ready")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    status_col.error("❌ Error")
    
    with col2:
        if st.button("🧹 Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
    
    with col3:
        st.write("")  # Spacer
    
    # Chat interface
    if st.session_state.data_loaded and st.session_state.agent:
        st.markdown("---")
        
        # Display chat history
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(
                        f'<div class="chat-message user"><b>You:</b> {message["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    answer = message["content"]
                    metadata = message.get("metadata", {})
                    
                    st.markdown(
                        f'<div class="chat-message assistant"><b>Agent:</b> {answer}</div>',
                        unsafe_allow_html=True
                    )
                    
                    if metadata:
                        st.markdown(
                            f'<div class="metadata">'
                            f'Intent: {metadata.get("intent", "unknown")} | '
                            f'Chunks: {metadata.get("chunks_used", 0)} | '
                            f'Transactions: {metadata.get("transactions_analyzed", 0)}'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                        if metadata.get("sources"):
                            st.markdown("**Sources:**")
                            sources_html = "".join([
                                f'<span class="source-badge">{src}</span>'
                                for src in metadata["sources"][:3]
                            ])
                            st.markdown(sources_html, unsafe_allow_html=True)
        
        # Input box
        st.markdown("---")
        
        user_input = st.text_input(
            "Ask a question about your spending:",
            placeholder="e.g., What's my top spending category?",
            key="user_input"
        )
        
        if user_input:
            # Add user message
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Get agent response
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.agent.process_query(user_input)
                    
                    # Add agent message
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "metadata": {
                            "intent": result.get("intent"),
                            "chunks_used": result.get("chunks_used"),
                            "transactions_analyzed": result.get("transactions_analyzed"),
                            "sources": result.get("sources")
                        }
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Example queries
        st.markdown("---")
        st.markdown("**Example queries:**")
        col1, col2, col3 = st.columns(3)
        
        examples = [
            "What's my top spending category?",
            "Show me all coffee purchases",
            "How much did I spend this month?"
        ]
        
        for i, example in enumerate(examples):
            with [col1, col2, col3][i]:
                if st.button(example, key=f"example_{i}"):
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": example
                    })
                    with st.spinner("Thinking..."):
                        result = st.session_state.agent.process_query(example)
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": result["answer"],
                            "metadata": {
                                "intent": result.get("intent"),
                                "chunks_used": result.get("chunks_used"),
                                "transactions_analyzed": result.get("transactions_analyzed"),
                                "sources": result.get("sources")
                            }
                        })
                    st.rerun()
    
    else:
        st.info("👆 Click 'Initialize Agent' above to get started!")

# ==================== TAB 2: DATA ====================

with tab2:
    st.markdown("### 📊 Data Processing Pipeline")
    
    st.markdown("#### Step 1: Generate Synthetic Data")
    
    if st.button("Generate Synthetic Bank Statement", key="gen_synthetic"):
        with st.spinner("Generating 12 months of synthetic transactions..."):
            try:
                from synthetic_data_generator import SyntheticDataGenerator
                
                generator = SyntheticDataGenerator(start_date="2024-01-01", months=12)
                df = generator.to_csv(synthetic_csv)
                
                st.success(f"✅ Generated {len(df)} transactions")
                st.dataframe(df.head(10))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Income", f"${df[df['category'] == 'Income']['amount'].sum():,.2f}")
                with col2:
                    st.metric("Total Expenses", f"${abs(df[df['category'] != 'Income']['amount'].sum()):,.2f}")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    st.markdown("#### Step 2: Process Documents")
    
    if st.button("Process Bank Statement", key="process_docs"):
        with st.spinner("Processing document..."):
            try:
                processor = DocumentProcessor(synthetic_csv)
                processor.process()
                processor.to_csv(processed_csv)
                
                st.success("✅ Document processed!")
                processor.print_summary()
                
                # Show summary
                summary = processor.get_summary()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Transactions", summary["total_transactions"])
                with col2:
                    st.metric("Recurring Charges", summary["recurring_count"])
                with col3:
                    st.metric("Anomalies", summary["anomaly_count"])
                
                # Show data
                st.dataframe(processor.df.head(10))
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    st.markdown("#### Step 3: Build Vector Database")
    
    if st.button("Build Chroma Database", key="build_chroma"):
        with st.spinner("Embedding and indexing data (this may take a minute)..."):
            try:
                pipeline = DataPipeline(
                    processed_csv=processed_csv,
                    chroma_db_path=chroma_path
                )
                result = pipeline.pipeline()
                
                if result:
                    st.success("✅ Vector database created!")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Monthly Summaries", result["summary_chunks"])
                    with col2:
                        st.metric("Transactions", result["transaction_chunks"])
                    with col3:
                        st.metric("Total Chunks", result["total_chunks"])
                    
                    # Test retrieval
                    st.markdown("**Test Retrieval:**")
                    test_queries = [
                        "coffee purchases",
                        "recurring charges",
                        "monthly expenses"
                    ]
                    
                    for query in test_queries:
                        pipeline.test_retrieval(query, n_results=3)
                else:
                    st.error("❌ Pipeline failed")
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    st.markdown("#### All Steps at Once")
    
    if st.button("🚀 Run Full Pipeline", key="run_full"):
        with st.spinner("Running full pipeline (Step 1-3)..."):
            try:
                # Step 1
                st.info("Step 1: Generating synthetic data...")
                from synthetic_data_generator import SyntheticDataGenerator
                generator = SyntheticDataGenerator(start_date="2024-01-01", months=12)
                generator.to_csv(synthetic_csv)
                st.success("✅ Synthetic data generated")
                
                # Step 2
                st.info("Step 2: Processing documents...")
                processor = DocumentProcessor(synthetic_csv)
                processor.process()
                processor.to_csv(processed_csv)
                st.success("✅ Documents processed")
                
                # Step 3
                st.info("Step 3: Building vector database...")
                pipeline = DataPipeline(processed_csv=processed_csv, chroma_db_path=chroma_path)
                result = pipeline.pipeline()
                st.success("✅ Vector database created")
                
                st.balloons()
                st.success("🎉 Full pipeline complete! Now initialize the agent in the Chat tab.")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ==================== TAB 3: ABOUT ====================

with tab3:
    st.markdown("""
    ### About This Project
    
    **Personal Finance RAG Agent** - "Your Money Therapist"
    
    This is a RAG (Retrieval-Augmented Generation) system that helps you understand your spending.
    
    #### How it works:
    
    1. **Upload** your bank statement (CSV)
    2. **Process** it - clean data, detect patterns
    3. **Embed** transactions and summaries into a vector database
    4. **Ask** questions in natural language
    5. **Get** answers powered by LLM reasoning
    
    #### Key Features:
    
    ✅ **Free & Private** - No subscriptions, your data stays with you
    ✅ **AI-Powered** - LLM reasoning with retrieval
    ✅ **Transparent** - See sources for all answers
    ✅ **Pattern Detection** - Finds recurring charges, anomalies, trends
    
    #### Technology Stack:
    
    - **LLM**: Mistral (via Ollama)
    - **Embeddings**: nomic-embed-text
    - **Vector DB**: Chroma
    - **Agent**: LangGraph
    - **UI**: Streamlit
    
    #### Example Questions:
    
    - What's my top spending category?
    - Show me all coffee purchases
    - How much did I spend on dining?
    - What are my subscriptions?
    - Am I spending more than last month?
    
    ---
    
    **Status**: MVP (Phase 1) - Basic Q&A working
    
    **Next Steps** (Phase 2):
    - Multi-month trend analysis
    - Budget predictions
    - Fine-tuning for better categorization
    - Support for multiple data sources
    
    ---
    
    Built with ❤️ as a portfolio piece
    """)
    
    st.markdown("---")
    st.markdown("""
    ### Getting Started
    
    1. Go to **Data** tab
    2. Click **Run Full Pipeline**
    3. Go to **Chat** tab
    4. Click **Initialize Agent**
    5. Start asking questions!
    """)

# ==================== FOOTER ====================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 0.9rem;">
    Personal Finance RAG Agent | Phase 1 MVP | 2026
</div>
""", unsafe_allow_html=True)