# data_pipeline.py

import pandas as pd
import json
from datetime import datetime
from typing import List, Dict
import chromadb
from chromadb.config import Settings
import requests
import os

class DataPipeline:
    """Process transactions into chunks and embed them in Chroma"""
    
    def __init__(self, processed_csv: str, chroma_db_path: str = "./chroma_vectordb"):
        """
        Initialize pipeline.
        
        Args:
            processed_csv: Path to processed_transactions.csv
            chroma_db_path: Path to store Chroma vector DB
        """
        self.processed_csv = processed_csv
        self.chroma_db_path = chroma_db_path
        self.df = None
        self.chroma_client = None
        self.collection = None
        self.embedding_model = "nomic-embed-text"
        self.ollama_url = "http://localhost:11434"
        
    def load_transactions(self) -> pd.DataFrame:
        """Load processed transactions"""
        self.df = pd.read_csv(self.processed_csv)
        self.df["date"] = pd.to_datetime(self.df["date"])
        print(f"✅ Loaded {len(self.df)} transactions")
        return self.df
    
    def check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                print(f"✅ Ollama is running at {self.ollama_url}")
                return True
        except Exception as e:
            print(f"❌ Ollama not found: {e}")
            print("   Please start Ollama with: ollama serve")
            print("   And pull the embedding model: ollama pull nomic-embed-text")
            return False
    
    def embed_text(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                print(f"❌ Embedding error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to embed: {e}")
            return None
    
    def create_monthly_summaries(self) -> List[Dict]:
        """Create monthly summary chunks"""
        summaries = []
        
        # Group by month
        for month, group in self.df.groupby("month_name"):
            # Calculate metrics
            income = group[group["amount"] > 0]["amount"].sum()
            expenses = group[group["amount"] < 0]["amount"].sum()
            net = income + expenses
            
            # Get category breakdown
            category_totals = group[group["amount"] < 0].groupby("category")["amount"].sum().to_dict()
            category_totals = {k: abs(v) for k, v in category_totals.items()}
            
            # Top merchants
            top_merchants = group[group["amount"] < 0]["merchant_clean"].value_counts().head(5).index.tolist()
            
            # Create text for embedding
            category_text = ", ".join([f"{cat}: ${amt:.2f}" for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)])
            
            text_for_embedding = (
                f"Month {month}: "
                f"Income ${income:.2f}, "
                f"Expenses ${abs(expenses):.2f}, "
                f"Net ${net:.2f}. "
                f"Categories: {category_text}. "
                f"Top merchants: {', '.join(top_merchants)}."
            )
            
            summary = {
                "id": f"summary_{month}",
                "chunk_type": "monthly_summary",
                "period": month,
                "income": income,
                "expenses": abs(expenses),
                "net": net,
                "category_breakdown": category_totals,
                "top_merchants": top_merchants,
                "transaction_count": len(group),
                "text": text_for_embedding,
                "metadata": json.dumps({
                    "period": month,
                    "income": float(income),
                    "expenses": float(abs(expenses)),
                    "net": float(net)
                })
            }
            
            summaries.append(summary)
        
        print(f"✅ Created {len(summaries)} monthly summary chunks")
        return summaries
    
    def create_transaction_chunks(self) -> List[Dict]:
        """Create individual transaction chunks"""
        chunks = []
        
        for idx, row in self.df.iterrows():
            # Skip balance-only rows (if any)
            if row["amount"] == 0:
                continue
            
            # Create text for embedding
            direction = "earned" if row["amount"] > 0 else "spent"
            amount_text = f"${abs(row['amount']):.2f}"
            recurring_text = "(recurring)" if row["is_recurring"] else ""
            anomaly_text = "[ANOMALY]" if row["is_anomaly"] else ""
            
            text_for_embedding = (
                f"{row['merchant_clean']} "
                f"{direction} {amount_text} "
                f"in {row['category']} "
                f"{recurring_text} {anomaly_text} "
                f"on {row['date'].strftime('%Y-%m-%d')}"
            ).strip()
            
            chunk = {
                "id": f"txn_{idx}",
                "chunk_type": "transaction",
                "date": row["date"].isoformat(),
                "merchant": row["merchant_clean"],
                "merchant_type": row["merchant_type"],
                "amount": float(row["amount"]),
                "category": row["category"],
                "is_recurring": bool(row["is_recurring"]),
                "is_anomaly": bool(row["is_anomaly"]),
                "month": row["month_name"],
                "text": text_for_embedding,
                "metadata": json.dumps({
                    "merchant": row["merchant_clean"],
                    "amount": float(row["amount"]),
                    "category": row["category"],
                    "date": row["date"].isoformat(),
                    "is_recurring": bool(row["is_recurring"]),
                    "is_anomaly": bool(row["is_anomaly"])
                })
            }
            
            chunks.append(chunk)
        
        print(f"✅ Created {len(chunks)} transaction chunks")
        return chunks
    
    def initialize_chroma(self) -> chromadb.Collection:
        """Initialize Chroma vector database (new API)"""
        # Create directory if needed
        os.makedirs(self.chroma_db_path, exist_ok=True)
    
        # New Chroma API: Use PersistentClient instead of Settings
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_db_path
        )
    
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="bank_transactions",
            metadata={"hnsw:space": "cosine"}
        )
    
        print(f"✅ Initialized Chroma at {self.chroma_db_path}")
        return self.collection
    
    def embed_and_store_chunks(self, chunks: List[Dict], chunk_type: str):
        """Embed chunks and store in Chroma"""
        print(f"\n🔄 Embedding and storing {chunk_type} chunks...")
        
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            # Embed the text
            embedding = self.embed_text(chunk["text"])
            
            if embedding is None:
                print(f"⚠️  Failed to embed chunk {chunk['id']}, skipping...")
                continue
            
            ids.append(chunk["id"])
            embeddings.append(embedding)
            documents.append(chunk["text"])
            metadatas.append({
                "chunk_type": chunk_type,
                "chunk_id": chunk["id"],
                **{k: str(v) for k, v in chunk.items() if k not in ["text", "id"]}
            })
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  ✓ Embedded {i + 1}/{len(chunks)}")
        
        # Add to Chroma collection
        if ids:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            print(f"✅ Stored {len(ids)} {chunk_type} chunks in Chroma")
        
        return len(ids)
    
    def pipeline(self) -> Dict:
        """Run full pipeline"""
        print("\n🚀 Starting Data Pipeline\n")
        print("=" * 50)
        
        # Step 1: Load data
        print("\n📂 Step 1: Load transactions")
        self.load_transactions()
        
        # Step 2: Check Ollama
        print("\n🤖 Step 2: Check Ollama")
        if not self.check_ollama():
            print("⚠️  Cannot proceed without Ollama. Start it and try again.")
            return None
        
        # Step 3: Create chunks
        print("\n✂️  Step 3: Create chunks")
        summaries = self.create_monthly_summaries()
        transactions = self.create_transaction_chunks()
        
        # Step 4: Initialize Chroma
        print("\n🗄️  Step 4: Initialize vector database")
        self.initialize_chroma()
        
        # Step 5: Embed and store
        print("\n🔧 Step 5: Embed and store")
        summary_count = self.embed_and_store_chunks(summaries, "monthly_summary")
        transaction_count = self.embed_and_store_chunks(transactions, "transaction")
        
        # Summary
        print("\n" + "=" * 50)
        print("✅ Pipeline Complete!")
        print(f"   Monthly Summaries: {summary_count}")
        print(f"   Transactions: {transaction_count}")
        print(f"   Total Chunks: {summary_count + transaction_count}")
        print(f"   Vector DB Location: {self.chroma_db_path}")
        print("=" * 50 + "\n")
        
        return {
            "summary_chunks": summary_count,
            "transaction_chunks": transaction_count,
            "total_chunks": summary_count + transaction_count,
            "chroma_path": self.chroma_db_path
        }
    
    def test_retrieval(self, query: str, n_results: int = 3):
        """Test similarity search"""
        if self.collection is None:
            print("❌ Collection not initialized. Run pipeline() first.")
            return
        
        # Embed the query
        query_embedding = self.embed_text(query)
        
        if query_embedding is None:
            print("❌ Failed to embed query")
            return
        
        # Search Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        print(f"\n🔍 Query: '{query}'")
        print(f"   Results ({n_results}):")
        
        if results["documents"]:
            for i, (doc, distance) in enumerate(zip(results["documents"][0], results["distances"][0])):
                print(f"   {i+1}. [{distance:.3f}] {doc[:100]}...")
        else:
            print("   No results found")


# Run it
if __name__ == "__main__":
    pipeline = DataPipeline(
        processed_csv="processed_transactions.csv",
        chroma_db_path="./chroma_vectordb"
    )
    
    # Run full pipeline
    result = pipeline.pipeline()
    
    # Test retrieval
    if result:
        print("\n🧪 Testing retrieval...\n")
        pipeline.test_retrieval("What did I spend on groceries?", n_results=5)
        pipeline.test_retrieval("Show me coffee purchases", n_results=5)
        pipeline.test_retrieval("recurring charges", n_results=5)