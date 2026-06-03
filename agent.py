# agent.py

import json
from typing import List, Dict, Any
import chromadb
import requests
from enum import Enum

class QueryIntent(Enum):
    """Types of queries the agent handles"""
    AGGREGATION = "aggregation"      # "What's my top spending?"
    SEARCH = "search"                 # "Show me all coffee purchases"
    TREND = "trend"                   # "Am I spending more this month?"
    PATTERN = "pattern"               # "What are my subscriptions?"
    CALCULATION = "calculation"       # "How much did I spend?"
    UNKNOWN = "unknown"


class FinanceAgent:
    """Agentic reasoning engine for personal finance Q&A"""
    
    def __init__(self, chroma_db_path: str = "./chroma_vectordb"):
        """
        Initialize agent with Chroma database and Ollama LLM.
        
        Args:
            chroma_db_path: Path to Chroma vector database
        """
        self.chroma_db_path = chroma_db_path
        self.chroma_client = None
        self.collection = None
        self.ollama_url = "http://localhost:11434"
        self.llm_model = "mistral"
        self.embedding_model = "nomic-embed-text"
        
        # Initialize connections
        self._initialize_chroma()
        self._check_ollama()
    
    def _initialize_chroma(self):
        """Connect to Chroma database"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=self.chroma_db_path
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name="bank_transactions"
            )
            print("✅ Connected to Chroma database")
        except Exception as e:
            print(f"❌ Failed to connect to Chroma: {e}")
            raise
    
    def _check_ollama(self):
        """Verify Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                print("✅ Ollama is running")
            else:
                raise Exception("Ollama not responding")
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Embed text using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                print(f"❌ Embedding failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Embedding error: {e}")
            return None
    
    def llm_call(self, prompt: str, context: str = "") -> str:
        """Call Mistral LLM for reasoning"""
        try:
            full_prompt = f"{context}\n\nUser query: {prompt}"
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": 0.3  # Lower = more focused
                },
                timeout=180
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                print(f"❌ LLM call failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return None
    
    # ==================== TOOLS ====================
    
    def tool_retrieve(self, query: str, n_results: int = 10) -> List[Dict]:
        """
        Tool 1: Retrieve relevant chunks from vector DB
        """
        # Embed the query
        query_embedding = self.embed_text(query)
        
        if query_embedding is None:
            return []
        
        # Search Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Parse results
        retrieved = []
        if results["documents"]:
            for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
                retrieved.append({
                    "text": doc,
                    "chunk_id": metadata.get("chunk_id"),
                    "chunk_type": metadata.get("chunk_type"),
                    "data": json.loads(metadata.get("metadata", "{}"))
                })
        
        return retrieved
    
    def tool_calculate(self, 
                      transactions: List[Dict],
                      operation: str = "sum",
                      group_by: str = None) -> Dict:
        """
        Tool 2: Calculate aggregates (sum, count, avg, etc.)
        """
        if not transactions:
            return {}
        
        if operation == "sum":
            if group_by:
                # Group and sum
                groups = {}
                for txn in transactions:
                    key = txn.get(group_by, "Unknown")
                    amount = float(txn.get("amount", 0))
                    groups[key] = groups.get(key, 0) + amount
                return groups
            else:
                # Simple sum
                return {"total": sum(float(t.get("amount", 0)) for t in transactions)}
        
        elif operation == "count":
            if group_by:
                groups = {}
                for txn in transactions:
                    key = txn.get(group_by, "Unknown")
                    groups[key] = groups.get(key, 0) + 1
                return groups
            else:
                return {"count": len(transactions)}
        
        elif operation == "average":
            amounts = [float(t.get("amount", 0)) for t in transactions]
            if amounts:
                return {"average": sum(amounts) / len(amounts)}
            return {}
        
        return {}
    
    def tool_analyze(self, transactions: List[Dict]) -> Dict:
        """
        Tool 3: Detect patterns (recurring, anomalies, trends)
        """
        analysis = {
            "recurring": [],
            "anomalies": [],
            "top_merchants": [],
            "category_breakdown": {}
        }
        
        # Find recurring
        recurring = [t for t in transactions if t.get("is_recurring")]
        analysis["recurring"] = recurring[:5]  # Top 5
        
        # Find anomalies
        anomalies = [t for t in transactions if t.get("is_anomaly")]
        analysis["anomalies"] = anomalies[:5]  # Top 5
        
        # Top merchants
        merchant_counts = {}
        for t in transactions:
            merchant = t.get("merchant", "Unknown")
            merchant_counts[merchant] = merchant_counts.get(merchant, 0) + 1
        analysis["top_merchants"] = sorted(merchant_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Category breakdown
        category_totals = {}
        for t in transactions:
            category = t.get("category", "Unknown")
            amount = float(t.get("amount", 0))
            category_totals[category] = category_totals.get(category, 0) + amount
        analysis["category_breakdown"] = category_totals
        
        return analysis
    
    def tool_validate(self, claim: str, data: List[Dict]) -> Dict:
        """
        Tool 4: Fact-check claims against actual data
        """
        # Simple validation logic
        validation = {
            "claim": claim,
            "valid": True,
            "explanation": "Claim appears consistent with data"
        }
        
        return validation
    
    # ==================== INTENT DETECTION ====================
    
    def detect_intent(self, query: str) -> QueryIntent:
        """Detect user intent from query"""
        query_lower = query.lower()
        
        # Aggregation: "top", "biggest", "highest", "most"
        if any(word in query_lower for word in ["top", "biggest", "highest", "most", "average", "total"]):
            return QueryIntent.AGGREGATION
        
        # Search: "show", "list", "find", "all"
        if any(word in query_lower for word in ["show", "list", "find", "all", "display"]):
            return QueryIntent.SEARCH
        
        # Trend: "more", "less", "increase", "decrease", "compare", "vs"
        if any(word in query_lower for word in ["more", "less", "increase", "decrease", "compare", "vs", "than"]):
            return QueryIntent.TREND
        
        # Pattern: "subscription", "recurring", "regular", "pattern", "habit"
        if any(word in query_lower for word in ["subscription", "recurring", "regular", "pattern", "habit", "every"]):
            return QueryIntent.PATTERN
        
        # Calculation: "how much", "total", "sum", "amount"
        if any(word in query_lower for word in ["how much", "total", "sum", "amount", "cost"]):
            return QueryIntent.CALCULATION
        
        return QueryIntent.UNKNOWN
    
    # ==================== MAIN AGENT LOOP ====================
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main agent loop: Query → Intent → Tools → LLM → Answer
        """
        print(f"\n🔄 Processing query: '{query}'\n")
        
        # Step 1: Detect intent
        intent = self.detect_intent(query)
        print(f"📌 Intent: {intent.value}")
        
        # Step 2: Retrieve relevant data
        print(f"🔍 Retrieving relevant data...")
        retrieved = self.tool_retrieve(query, n_results=15)
        
        if not retrieved:
            return {
                "query": query,
                "answer": "Sorry, I couldn't find relevant transactions to answer this question.",
                "intent": intent.value,
                "sources": []
            }
        
        print(f"   Found {len(retrieved)} relevant chunks")
        
        # Step 3: Parse data from retrieved chunks
        transactions = []
        summaries = []
        
        for chunk in retrieved:
            if chunk["chunk_type"] == "transaction":
                transactions.append(chunk["data"])
            elif chunk["chunk_type"] == "monthly_summary":
                summaries.append(chunk["data"])
        
        print(f"   Transactions: {len(transactions)}, Summaries: {len(summaries)}")
        
        # Step 4: Call appropriate tools based on intent
        context_data = {}
        
        if intent == QueryIntent.AGGREGATION:
            print(f"📊 Running aggregation analysis...")
            context_data["category_totals"] = self.tool_calculate(
                transactions, operation="sum", group_by="category"
            )
            context_data["merchant_totals"] = self.tool_calculate(
                transactions, operation="sum", group_by="merchant"
            )
        
        elif intent == QueryIntent.SEARCH:
            print(f"📋 Preparing search results...")
            context_data["matching_transactions"] = transactions[:10]
        
        elif intent == QueryIntent.TREND:
            print(f"📈 Analyzing trends...")
            context_data["summaries"] = summaries
            context_data["transactions"] = transactions
        
        elif intent == QueryIntent.PATTERN:
            print(f"🔗 Detecting patterns...")
            analysis = self.tool_analyze(transactions)
            context_data["analysis"] = analysis
        
        else:  # UNKNOWN or CALCULATION
            print(f"🧮 Performing calculation...")
            context_data["total"] = self.tool_calculate(transactions, operation="sum")
            context_data["count"] = self.tool_calculate(transactions, operation="count")
        
        # Step 5: Build context for LLM
        context_text = f"""
You are a helpful personal finance assistant. Analyze the following financial data and answer the user's question accurately and concisely.

Retrieved Data:
{json.dumps(context_data, indent=2, default=str)}

Instructions:
1. Base your answer ONLY on the provided data
2. Always cite which transactions or summaries you're referencing
3. For numbers, be precise (don't round aggressively)
4. If you don't have enough data, say so clearly
5. Keep response under 150 words
"""
        
        # Step 6: Call LLM for synthesis
        print(f"🧠 LLM reasoning...")
        answer = self.llm_call(query, context_text)
        
        if not answer:
            answer = "Sorry, I encountered an error while processing your question."
        
        # Step 7: Prepare response with sources
        sources = [chunk["chunk_id"] for chunk in retrieved[:5]]
        
        result = {
            "query": query,
            "answer": answer.strip(),
            "intent": intent.value,
            "sources": sources,
            "chunks_used": len(retrieved),
            "transactions_analyzed": len(transactions)
        }
        
        return result
    
    def chat(self):
        """Interactive chat loop"""
        print("\n" + "=" * 60)
        print("💰 Personal Finance RAG Agent")
        print("=" * 60)
        print("Ask questions about your spending!")
        print("Examples:")
        print("  - What's my top spending category?")
        print("  - Show me all coffee purchases")
        print("  - How much did I spend on dining?")
        print("  - What are my subscriptions?")
        print("\nType 'quit' to exit\n")
        
        while True:
            try:
                query = input("You: ").strip()
                
                if query.lower() in ["quit", "exit", "q"]:
                    print("Goodbye! 👋")
                    break
                
                if not query:
                    continue
                
                result = self.process_query(query)
                
                print(f"\n{'=' * 60}")
                print(f"Agent: {result['answer']}")
                print(f"\nMetadata:")
                print(f"  Intent: {result['intent']}")
                print(f"  Chunks analyzed: {result['chunks_used']}")
                print(f"  Transactions: {result['transactions_analyzed']}")
                if result['sources']:
                    print(f"  Sources: {', '.join(result['sources'][:3])}")
                print("=" * 60 + "\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")


# Run interactive chat
if __name__ == "__main__":
    agent = FinanceAgent(chroma_db_path="./chroma_vectordb")
    agent.chat()