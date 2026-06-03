# document_processor.py

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple
from collections import Counter

class DocumentProcessor:
    """Process bank statements and enrich with metadata"""
    
    def __init__(self, csv_file: str):
        """
        Initialize processor with CSV file.
        
        Args:
            csv_file: Path to bank statement CSV
        """
        self.csv_file = csv_file
        self.df = None
        self.transactions = None
        
    def load_csv(self) -> pd.DataFrame:
        """Load and validate CSV file"""
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"✅ Loaded {len(self.df)} rows from {self.csv_file}")
            
            # Validate required columns
            required_cols = ["date", "merchant", "amount", "balance", "category"]
            missing = [col for col in required_cols if col not in self.df.columns]
            
            if missing:
                raise ValueError(f"❌ Missing columns: {missing}")
            
            # Parse dates
            self.df["date"] = pd.to_datetime(self.df["date"])
            
            # Validate amounts are numeric
            self.df["amount"] = pd.to_numeric(self.df["amount"], errors="coerce")
            
            if self.df["amount"].isna().any():
                raise ValueError("❌ Some amounts are not valid numbers")
            
            print(f"✅ CSV validation passed")
            return self.df
            
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            raise
    
    def clean_merchants(self) -> pd.DataFrame:
        """Normalize merchant names"""
        # Remove extra spaces and convert to uppercase
        self.df["merchant_clean"] = (
            self.df["merchant"]
            .str.strip()
            .str.upper()
        )
        
        # Remove common suffixes
        suffixes = [" #.*", " INC", " LLC", " CO", " CORP"]
        for suffix in suffixes:
            self.df["merchant_clean"] = self.df["merchant_clean"].str.replace(
                suffix, "", regex=True
            )
        
        # Remove location codes (e.g., "STARBUCKS COFFEE #1234" -> "STARBUCKS COFFEE")
        self.df["merchant_clean"] = self.df["merchant_clean"].str.replace(
            r"#\d+", "", regex=True
        ).str.strip()
        
        print(f"✅ Merchant names cleaned")
        return self.df
    
    def detect_recurring(self) -> pd.DataFrame:
        """Detect recurring transactions (same merchant, same amount, regular interval)"""
        self.df["is_recurring"] = False
        
        # Group by cleaned merchant and amount
        for (merchant, amount), group in self.df.groupby(["merchant_clean", "amount"]):
            if amount == 0:
                continue
            
            # Need at least 2 occurrences
            if len(group) < 2:
                continue
            
            # Check if dates are roughly monthly (within 25-35 days)
            dates = sorted(group["date"].values)
            intervals = []
            
            for i in range(1, len(dates)):
                delta = (pd.Timestamp(dates[i]) - pd.Timestamp(dates[i-1])).days
                intervals.append(delta)
            
            # If most intervals are 25-35 days apart, it's recurring
            if len(intervals) > 0:
                avg_interval = np.mean(intervals)
                if 25 <= avg_interval <= 35:  # Roughly monthly
                    self.df.loc[group.index, "is_recurring"] = True
        
        recurring_count = self.df["is_recurring"].sum()
        print(f"✅ Detected {recurring_count} recurring transactions")
        return self.df
    
    def detect_anomalies(self, threshold_std: float = 2.5) -> pd.DataFrame:
        """Detect anomalous transactions (statistical outliers)"""
        self.df["is_anomaly"] = False
        
        # Separate by income/expense
        expenses = self.df[self.df["amount"] < 0].copy()
        
        if len(expenses) > 0:
            # Calculate z-score for each transaction
            amounts = expenses["amount"].abs()
            mean = amounts.mean()
            std = amounts.std()
            
            # Flag outliers (beyond threshold standard deviations)
            z_scores = np.abs((amounts - mean) / std)
            outliers = z_scores > threshold_std
            
            self.df.loc[expenses[outliers].index, "is_anomaly"] = True
        
        anomaly_count = self.df["is_anomaly"].sum()
        print(f"✅ Detected {anomaly_count} anomalies")
        return self.df
    
    def infer_merchant_type(self) -> pd.DataFrame:
        """Infer merchant type (e.g., Coffee, Grocery, Gas, etc.)"""
        
        # Define keywords for common merchant types
        merchant_keywords = {
            "Coffee": ["STARBUCKS", "COFFEE", "CAFE"],
            "Grocery": ["WHOLE FOODS", "KROGER", "TRADER JOES", "COSTCO", "SAFEWAY"],
            "Restaurant": ["CHIPOTLE", "OLIVE GARDEN", "PANERA", "PIZZA", "CHICK-FIL-A", "TACO BELL"],
            "Gas": ["SHELL", "CHEVRON", "EXXON", "GAS STATION"],
            "Online": ["AMAZON", "EBAY"],
            "Retail": ["TARGET", "WALMART", "HOME DEPOT", "BEST BUY"],
            "Subscription": ["NETFLIX", "SPOTIFY", "AWS"],
            "Utilities": ["ELECTRIC", "WATER", "GAS COMPANY", "INTERNET"],
            "Income": ["EMPLOYER", "PAYCHECK", "SALARY"],
        }
        
        self.df["merchant_type"] = "Other"
        
        for merchant_type, keywords in merchant_keywords.items():
            mask = self.df["merchant_clean"].str.contains(
                "|".join(keywords), regex=True, na=False
            )
            self.df.loc[mask, "merchant_type"] = merchant_type
        
        print(f"✅ Merchant types inferred")
        return self.df
    
    def add_month_year(self) -> pd.DataFrame:
        """Add month and year columns for easy grouping"""
        self.df["month"] = self.df["date"].dt.to_period("M")
        self.df["year"] = self.df["date"].dt.year
        self.df["month_name"] = self.df["date"].dt.strftime("%Y-%m")
        
        print(f"✅ Month/year columns added")
        return self.df
    
    def process(self) -> pd.DataFrame:
        """Run full processing pipeline"""
        print("\n🔄 Starting document processing pipeline...\n")
        
        self.load_csv()
        self.clean_merchants()
        self.detect_recurring()
        self.detect_anomalies()
        self.infer_merchant_type()
        self.add_month_year()
        
        print("\n✅ Processing complete!\n")
        return self.df
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if self.df is None:
            raise ValueError("❌ Call process() first")
        
        summary = {
            "total_transactions": len(self.df),
            "date_range": (self.df["date"].min(), self.df["date"].max()),
            "total_income": self.df[self.df["amount"] > 0]["amount"].sum(),
            "total_expenses": abs(self.df[self.df["amount"] < 0]["amount"].sum()),
            "net": self.df["amount"].sum(),
            "recurring_count": self.df["is_recurring"].sum(),
            "anomaly_count": self.df["is_anomaly"].sum(),
            "categories": self.df["category"].unique().tolist(),
            "merchant_types": self.df["merchant_type"].unique().tolist(),
        }
        
        return summary
    
    def print_summary(self):
        """Print formatted summary"""
        summary = self.get_summary()
        
        print("\n📊 Data Summary")
        print("=" * 50)
        print(f"Total Transactions: {summary['total_transactions']}")
        print(f"Date Range: {summary['date_range'][0].date()} to {summary['date_range'][1].date()}")
        print(f"Total Income: ${summary['total_income']:,.2f}")
        print(f"Total Expenses: ${summary['total_expenses']:,.2f}")
        print(f"Net: ${summary['net']:,.2f}")
        print(f"Recurring Charges: {summary['recurring_count']}")
        print(f"Anomalies Detected: {summary['anomaly_count']}")
        print(f"\nCategories: {', '.join(summary['categories'])}")
        print(f"Merchant Types: {', '.join(summary['merchant_types'])}")
        print("=" * 50 + "\n")
    
    def to_csv(self, output_file: str = "processed_transactions.csv"):
        """Export processed data to CSV"""
        if self.df is None:
            raise ValueError("❌ Call process() first")
        
        self.df.to_csv(output_file, index=False)
        print(f"✅ Processed data saved to: {output_file}")
        return output_file


# Run it
if __name__ == "__main__":
    # Process the synthetic data from Step 1
    processor = DocumentProcessor("synthetic_bank_statement.csv")
    processor.process()
    processor.print_summary()
    processor.to_csv("processed_transactions.csv")