# synthetic_data_generator.py

import pandas as pd
import random
from datetime import datetime, timedelta
from typing import List, Dict

class SyntheticDataGenerator:
    def __init__(self, start_date: str = "2025-01-01", months: int = 12):
        """
        Generate 12 months of realistic bank transactions.
        
        Args:
            start_date: Start date in format "YYYY-MM-DD"
            months: Number of months to generate (default: 12)
        """
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.months = months
        self.transactions = []
        self.balance = 5000  # Starting balance
        
    def add_salary(self, amount: int = 3500, day: int = 1, variance: int = 100):
        """Add monthly salary (income)"""
        current_date = self.start_date
        
        for _ in range(self.months):
            # Set to salary day of the month
            salary_date = current_date.replace(day=day)
            
            # Add slight variance
            salary_amount = amount + random.randint(-variance, variance)
            
            self.transactions.append({
                "date": salary_date,
                "merchant": "EMPLOYER PAYCHECK",
                "amount": salary_amount,
                "category": "Income",
                "description": "Monthly salary"
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    def add_recurring_charge(self, 
                            merchant: str, 
                            amount: float, 
                            day: int = 5,
                            category: str = "Subscriptions"):
        """Add recurring monthly charge (rent, subscriptions, etc.)"""
        current_date = self.start_date
        
        for _ in range(self.months):
            try:
                charge_date = current_date.replace(day=day)
            except ValueError:
                # Handle months with fewer days (e.g., Feb)
                charge_date = current_date.replace(day=28)
            
            self.transactions.append({
                "date": charge_date,
                "merchant": merchant,
                "amount": -amount,
                "category": category,
                "description": f"Monthly {merchant.lower()}"
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    def add_variable_spending(self,
                             merchant_pattern: List[str],
                             amount_range: tuple,
                             frequency_per_month: float,
                             category: str):
        """
        Add variable spending (groceries, dining, etc.)
        
        Args:
            merchant_pattern: List of possible merchant names
            amount_range: Tuple (min, max) for transaction amount
            frequency_per_month: How many times per month (e.g., 2.5 = 2-3 times)
            category: Transaction category
        """
        current_date = self.start_date
        
        for month_idx in range(self.months):
            # Randomize frequency slightly
            num_transactions = int(frequency_per_month) + (1 if random.random() < (frequency_per_month % 1) else 0)
            
            # Distribute randomly throughout the month
            for _ in range(num_transactions):
                day_offset = random.randint(1, 28)
                txn_date = current_date + timedelta(days=day_offset)
                
                merchant = random.choice(merchant_pattern)
                amount = round(random.uniform(amount_range[0], amount_range[1]), 2)
                
                self.transactions.append({
                    "date": txn_date,
                    "merchant": merchant,
                    "amount": -amount,
                    "category": category,
                    "description": f"Purchase at {merchant}"
                })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
    
    def add_anomalies(self):
        """Add one-time, unusual transactions"""
        anomalies = [
            {"date": self.start_date + timedelta(days=45), "merchant": "UNITED AIRLINES", "amount": -450, "category": "Travel"},
            {"date": self.start_date + timedelta(days=120), "merchant": "BEST BUY ELECTRONICS", "amount": -899, "category": "Electronics"},
            {"date": self.start_date + timedelta(days=200), "merchant": "COACHELLA TICKETS", "amount": -250, "category": "Entertainment"},
            {"date": self.start_date + timedelta(days=280), "merchant": "APPLE REFUND", "amount": 99, "category": "Returns"},
        ]
        
        for anomaly in anomalies:
            self.transactions.append(anomaly)
    
    def generate(self) -> pd.DataFrame:
        """Generate all transactions and return as DataFrame"""
        # Add income
        self.add_salary(amount=3500, day=1, variance=100)
        
        # Add fixed recurring charges
        self.add_recurring_charge("LANDLORD RENT", 1500, day=5, category="Housing")
        self.add_recurring_charge("NETFLIX SUBSCRIPTION", 14.99, day=10, category="Subscriptions")
        self.add_recurring_charge("SPOTIFY PREMIUM", 9.99, day=12, category="Subscriptions")
        self.add_recurring_charge("AWS CLOUD SERVICES", 50, day=15, category="Utilities & Services")
        
        # Add variable spending
        self.add_variable_spending(
            merchant_pattern=[
                "WHOLE FOODS MARKET",
                "KROGER GROCERY",
                "TRADER JOES",
                "COSTCO WHOLESALE",
                "SAFEWAY"
            ],
            amount_range=(40, 150),
            frequency_per_month=2.5,
            category="Groceries"
        )
        
        self.add_variable_spending(
            merchant_pattern=[
                "STARBUCKS COFFEE",
                "CHIPOTLE MEXICAN",
                "PANERA BREAD",
                "OLIVE GARDEN",
                "CHICK-FIL-A",
                "TACO BELL",
                "PIZZA HUT",
                "SUBWAY SANDWICHES"
            ],
            amount_range=(8, 45),
            frequency_per_month=3.5,
            category="Dining & Restaurants"
        )
        
        self.add_variable_spending(
            merchant_pattern=[
                "SHELL GAS STATION",
                "CHEVRON GAS STATION",
                "EXXON MOBIL"
            ],
            amount_range=(35, 65),
            frequency_per_month=2,
            category="Gas & Transport"
        )
        
        self.add_variable_spending(
            merchant_pattern=[
                "AMAZON.COM",
                "TARGET STORE",
                "WALMART",
                "HOME DEPOT"
            ],
            amount_range=(15, 120),
            frequency_per_month=1.5,
            category="Shopping & Retail"
        )
        
        # Add anomalies
        self.add_anomalies()
        
        # Sort by date
        self.transactions.sort(key=lambda x: x["date"])
        
        # Calculate running balance
        balance = self.balance
        for txn in self.transactions:
            balance += txn["amount"]
            txn["balance"] = round(balance, 2)
        
        # Convert to DataFrame
        df = pd.DataFrame(self.transactions)
        df["date"] = pd.to_datetime(df["date"])
        df = df[["date", "merchant", "amount", "balance", "category", "description"]]
        
        return df
    
    def to_csv(self, filename: str = "synthetic_bank_statement1.csv"):
        """Export to CSV"""
        df = self.generate()
        df.to_csv(filename, index=False)
        print(f"✅ Generated {len(df)} transactions")
        print(f"📁 Saved to: {filename}")
        print(f"\nDataset Summary:")
        print(f"  Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"  Total income: ${df[df['category'] == 'Income']['amount'].sum():.2f}")
        print(f"  Total expenses: ${abs(df[df['category'] != 'Income']['amount'].sum()):.2f}")
        print(f"  Net: ${df['amount'].sum():.2f}")
        print(f"\nCategories:")
        print(df.groupby('category')['amount'].sum().sort_values())
        
        return df


# Run it
if __name__ == "__main__":
    generator = SyntheticDataGenerator(start_date="2024-01-01", months=12)
    df = generator.to_csv("synthetic_bank_statement.csv")