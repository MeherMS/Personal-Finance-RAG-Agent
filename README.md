# 💰 Personal Finance RAG Agent - "Your Money Therapist"

An AI-powered personal finance assistant that helps you understand your spending through natural language conversations. Upload your bank statements and ask questions about your financial patterns, trends, and spending habits.

**Status**: Phase 1 MVP ✅ | Chat-based Q&A working

---

## 🎯 Features

✅ **Free & Private** - No subscriptions, no data collection  
✅ **AI-Powered** - LLM-based reasoning with retrieval-augmented generation  
✅ **Natural Language** - Ask questions like a human  
✅ **Pattern Detection** - Automatically finds recurring charges, anomalies, trends  
✅ **Transparent** - See sources for all answers  
✅ **Local-First** - All processing happens on your machine  

---

## 📋 Prerequisites

### Required
- **Python 3.10+**
- **Ollama** (for LLM + embeddings)
  - Download: https://ollama.ai
  - Required models:
    - `mistral` (7B LLM for reasoning)
    - `nomic-embed-text` (embeddings for retrieval)

### Install Ollama Models
```bash
# Start Ollama server (run in a separate terminal)
ollama serve

# In another terminal, pull the models
ollama pull mistral
ollama pull nomic-embed-text

# Verify both models are available
ollama list
```

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/MeherMS/Personal-Finance-RAG-Agent.git
cd Personal-Finance-RAG-Agent
```

### 2. Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚡ Quick Start

### Step 1: Generate Synthetic Data
```bash
python synthetic_data_generator.py
```
**Output**: `synthetic_bank_statement.csv` (12 months of realistic transactions)

### Step 2: Process Documents
```bash
python document_processor.py
```
**Output**: `processed_transactions.csv` (cleaned, enriched data)

### Step 3: Build Vector Database
```bash
python data_pipeline.py
```
**Prerequisites**: Ollama must be running (`ollama serve`)  
**Output**: `chroma_vectordb/` (indexed embeddings)

### Step 4: Start Interactive Chat
```bash
python agent.py
```
**Talk to your finance data!**

---

## 💬 Example Queries

Once the agent is running, try:
You: What's my top spending category?
Agent: Based on your transactions, your top spending category is Dining & Restaurants with $1,350.00 (estimated from 40+ transactions). The second is Groceries at $960.00.
You: Show me all coffee purchases
Agent: I found 18 coffee purchases over the period...
You: How much did I spend on subscriptions?
Agent: Your total subscription spending is $287.88, including Netflix ($14.99/month), Spotify ($9.99/month), and AWS ($50/month).
You: What are my anomalies?
Agent: I detected 4 unusual transactions: United Airlines ($450), Best Buy Electronics ($899), Coachella Tickets ($250), and Apple Refund ($99).

---

## 🏗️ Architecture
Data Input (Bank Statement CSV)
↓
Document Processor (clean, enrich metadata)
↓
Data Pipeline (chunk, embed, index)
↓
Vector Database (Chroma)
↓
LangGraph Agent (intent detection, tool calling)
↓
LLM (Mistral via Ollama)
↓
Natural Language Response

### Components

| Component | Purpose | Tech |
|-----------|---------|------|
| **Synthetic Data Generator** | Create realistic transaction data | Python + pandas |
| **Document Processor** | Clean, validate, enrich transactions | pandas + pydantic |
| **Data Pipeline** | Chunk data, generate embeddings, index | Chroma + Ollama |
| **Vector Database** | Store and retrieve relevant chunks | Chroma (local) |
| **Agent** | Intent detection, tool calling, reasoning | LangGraph |
| **LLM** | Natural language reasoning | Mistral (Ollama) |

---

## 📁 Project Structure
Personal-Finance-RAG-Agent/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── synthetic_data_generator.py        # Generate fake bank data
├── document_processor.py               # Parse & enrich CSV
├── data_pipeline.py                    # Embed & index data
├── agent.py                            # Interactive chat agent
│
├── synthetic_bank_statement.csv       # Generated (Step 1)
├── processed_transactions.csv         # Generated (Step 2)
└── chroma_vectordb/                   # Generated (Step 3)
└── [vector database files]

---

## 🔄 Workflow

### Full Pipeline (One-Time Setup)
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run pipeline
python synthetic_data_generator.py
python document_processor.py
python data_pipeline.py

# Terminal 2: Chat with your data
python agent.py
```

### Interactive Chat Only (After Setup)
```bash
# Terminal 1: Ollama (if not running)
ollama serve

# Terminal 2: Start chatting
python agent.py
```

---

## 🛠️ How It Works

### 1. Data Processing
- **Input**: Bank statement CSV
- **Processing**:
  - Cleans merchant names
  - Detects recurring charges (monthly patterns)
  - Flags anomalies (statistical outliers)
  - Infers merchant types (Coffee, Grocery, etc.)
- **Output**: Enriched transaction data

### 2. Embedding & Indexing
- **Chunks**: Creates two types
  - Monthly summaries (fast for trend queries)
  - Individual transactions (detailed searches)
- **Embeddings**: Uses `nomic-embed-text` to convert text→vectors
- **Storage**: Local Chroma database (no cloud upload)

### 3. Agent Reasoning
- **Intent Detection**: Understands query type (aggregation, search, trend, pattern)
- **Retrieval**: Finds most relevant chunks from vector DB
- **Tool Calling**: Aggregates, analyzes, validates data
- **Synthesis**: Uses Mistral LLM to generate natural response
- **Citations**: Includes sources for transparency

---

## 📊 Supported Query Types

| Query Type | Examples |
|-----------|----------|
| **Aggregation** | "Top spending category?" "Average transaction?" |
| **Search** | "Show me coffee purchases" "List all dining" |
| **Trend** | "Spending more this month?" "Dining trend?" |
| **Pattern** | "What are my subscriptions?" "Recurring charges?" |
| **Calculation** | "Total spent?" "How much on groceries?" |

---

## 🎯 Features (Current Phase)

✅ Parse and process bank statements (CSV)  
✅ Detect recurring charges automatically  
✅ Detect anomalies (unusual transactions)  
✅ Generate embeddings with Ollama  
✅ Index in local Chroma vector database  
✅ Intent-based query routing  
✅ Tool-based reasoning (retrieve, calculate, analyze)  
✅ Natural language responses from Mistral LLM  
✅ Source citations  
✅ Interactive chat interface  

---

## 🚧 Roadmap

### Phase 2 (Coming Soon)
- [ ] Multi-month trend analysis
- [ ] Budget scenario planning
- [ ] Improved pattern detection
- [ ] Better error handling
- [ ] Performance optimization

### Phase 3
- [ ] Credit card support
- [ ] Investment account statements
- [ ] Fine-tuned categorization model
- [ ] Predictive budgeting
- [ ] Web UI (Streamlit)

### Phase 4
- [ ] Multi-user support
- [ ] Data persistence
- [ ] Mobile app
- [ ] Cloud deployment

---

## ⚙️ Configuration

### Customize Models
Edit the model names in `agent.py`:
```python
self.llm_model = "mistral"              # Change LLM
self.embedding_model = "nomic-embed-text"  # Change embeddings
```

### Customize Date Range
In `synthetic_data_generator.py`:
```python
generator = SyntheticDataGenerator(
    start_date="2024-01-01",  # Change start date
    months=12                  # Change number of months
)
```

---

## 🐛 Troubleshooting

### Error: "Connection refused" (Ollama not running)
```bash
# Start Ollama in a separate terminal
ollama serve

# Verify models are available
ollama list
```

### Error: "Model not found"
```bash
# Download missing models
ollama pull mistral
ollama pull nomic-embed-text
```

### Error: "Chroma database not found"
```bash
# Rebuild the vector database
python data_pipeline.py
```

### Slow embeddings
- First embedding takes longer (model loading)
- Subsequent embeddings are faster
- Consider using GPU if available

---

## 📈 Performance

| Task | Time | Notes |
|------|------|-------|
| Generate synthetic data | ~1s | 350 transactions |
| Process documents | ~2s | Clean + enrich |
| Build vector DB | ~30-60s | Depends on Ollama speed |
| First query | ~5-10s | Model loading |
| Subsequent queries | ~2-3s | Faster |

---

## 💾 Data Privacy

✅ **All local** - Data never leaves your machine  
✅ **Synthetic by default** - Demo uses fake data  
✅ **Your control** - Replace with real data if desired  
✅ **No cloud uploads** - No API keys needed (except optional HF)  

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

MIT License - feel free to use for personal or commercial projects

---

## 📚 References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Chroma Documentation](https://docs.trychroma.com/)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [Mistral Model](https://mistral.ai/)

---

## 🙋 Support

- **Issues**: Open a GitHub issue
- **Questions**: Discussions tab
- **Discord**: [Join our community]

---

## 📊 Project Status

- **Phase**: 1 (MVP)
- **Last Updated**: January 2025
- **Stability**: Alpha (use at your own risk)
- **Python Version**: 3.10+

---

## 🎓 Learning Resources

This project demonstrates:
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ LLM agentic workflows
- ✅ Vector embeddings and similarity search
- ✅ Natural language processing
- ✅ Data processing pipelines
- ✅ Python best practices

Perfect for learning or portfolio building!

---

**Built with ❤️ as a personal finance solution and learning project**
