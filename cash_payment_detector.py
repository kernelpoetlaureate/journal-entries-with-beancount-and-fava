#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cash Payment Detector for Georgian Sales Data
Analyzes report(18).xlsx to identify cash payments and generates appropriate Beancount entries
"""

import pandas as pd
import sys
from datetime import datetime
import re


class CashPaymentDetector:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.df = None
        
        # Column mappings for sales data with cash detection
        self.column_map = {
            'ორგანიზაცია': 'organization',      # Customer/Organization
            'თანხა': 'amount',                  # Amount (VAT included)
            'გააქტიურების თარ.': 'date',         # Sale Date
            'დანიშნულება': 'payment_method',   # Payment method column - KEY COLUMN!
        }
        
        # Cash payment indicators in Georgian
        self.cash_indicators = [
            'ნაღდი',        # Cash
            'ნაღ',          # Cash (abbreviated)
            'კეში',         # Cash (transliterated)
            'cash',         # English
            'ნაღდი ფული',   # Cash money
        ]
        
        # Account structure
        self.sales_account = "Income:Sales"
        self.vat_account = "Liabilities:VAT:Output"
        self.cash_account = "Assets:Cash"
        self.receivables_account = "Assets:Receivables"
        
        # VAT rate (18%)
        self.vat_rate = 0.18
        
        # Default currency
        self.default_currency = "GEL"
        
    def load_data(self):
        """Load Excel data and identify cash payments"""
        try:
            self.df = pd.read_excel(self.excel_file_path, engine='xlrd')
            print(f"Successfully loaded {len(self.df)} rows from Excel file")
            
            # Print available columns for debugging
            print("Available columns:")
            for i, col in enumerate(self.df.columns):
                print(f"  {i}: {col}")
            
            # Keep only the columns we need
            needed_columns = list(self.column_map.keys())
            
            # Check if all needed columns exist
            missing_columns = [col for col in needed_columns if col not in self.df.columns]
            if missing_columns:
                print(f"Warning: Missing columns: {missing_columns}")
                print(f"Available columns: {list(self.df.columns)}")
            
            # Filter to only needed columns and rename
            available_columns = [col for col in needed_columns if col in self.df.columns]
            self.df = self.df[available_columns]
            self.df = self.df.rename(columns=self.column_map)
            
            # Remove rows with missing essential data
            self.df = self.df.dropna(subset=['organization', 'amount'])
            
            # Clean amounts and filter out zero/negative amounts
            self.df['amount'] = self.df['amount'].apply(self.clean_amount)
            self.df = self.df[self.df['amount'] > 0]
            
            # Detect cash payments
            self.df['is_cash_payment'] = self.df['payment_method'].apply(self.is_cash_payment)
            
            cash_count = self.df['is_cash_payment'].sum()
            total_count = len(self.df)
            
            print(f"Processed {total_count} valid transactions")
            print(f"Identified {cash_count} cash payments ({cash_count/total_count*100:.1f}%)")
            
            return True
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            return False
    
    def clean_amount(self, amount):
        """Clean and convert amount to float"""
        if pd.isna(amount):
            return 0.0
        
        if isinstance(amount, str):
            # Remove any non-numeric characters except decimal point and minus
            cleaned = re.sub(r'[^\d.-]', '', str(amount))
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        
        return float(amount)
    
    def is_cash_payment(self, payment_method):
        """Check if payment method indicates cash payment"""
        if pd.isna(payment_method):
            return False
        
        payment_str = str(payment_method).lower().strip()
        
        # Check for cash indicators
        for indicator in self.cash_indicators:
            if indicator.lower() in payment_str:
                return True
        
        return False
    
    def format_date(self, date_value):
        """Convert date to Beancount format (YYYY-MM-DD)"""
        if pd.isna(date_value):
            return datetime.now().strftime('%Y-%m-%d')
        
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        
        # Try to parse string dates
        try:
            if isinstance(date_value, str):
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%Y']:
                    try:
                        parsed_date = datetime.strptime(date_value, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
            
            # If it's a number (Excel date serial)
            if isinstance(date_value, (int, float)):
                # Excel date serial number (days since 1900-01-01)
                base_date = datetime(1900, 1, 1)
                actual_date = base_date + pd.Timedelta(days=date_value-2)  # Excel quirk
                return actual_date.strftime('%Y-%m-%d')
        except:
            pass
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def clean_organization_name(self, org_name):
        """Clean organization name to create valid Beancount account names"""
        if pd.isna(org_name):
            return "Unknown"
        
        # Convert to string and clean
        clean_name = str(org_name).strip()
        
        # Replace problematic characters for account names
        # Keep Georgian characters, letters, numbers, and some symbols
        clean_name = re.sub(r'[^\w\s\-\(\)ა-ჰ]', '', clean_name)
        
        # Replace spaces and special characters with hyphens
        clean_name = re.sub(r'[\s\-\(\)]+', '-', clean_name)
        
        # Remove leading/trailing hyphens and underscores
        clean_name = clean_name.strip('-_')
        
        # Ensure it starts with a letter or number (Beancount requirement)
        if clean_name and not clean_name[0].isalnum():
            clean_name = 'C' + clean_name  # Prefix with 'C' for Customer
        
        # Replace any remaining underscores with hyphens
        clean_name = clean_name.replace('_', '-')
        
        # Limit length for readability
        if len(clean_name) > 50:
            clean_name = clean_name[:50]
        
        return clean_name if clean_name else "Unknown"
    
    def calculate_vat_amounts(self, total_amount):
        """Calculate VAT and net amounts from VAT-inclusive total"""
        net_amount = total_amount / (1 + self.vat_rate)
        vat_amount = total_amount - net_amount
        return net_amount, vat_amount
    
    def get_cash_transactions(self):
        """Get only transactions that were paid in cash"""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df['is_cash_payment'] == True]
    
    def get_non_cash_transactions(self):
        """Get transactions that were NOT paid in cash (should be receivables)"""
        if self.df is None:
            return pd.DataFrame()
        
        return self.df[self.df['is_cash_payment'] == False]
    
    def export_cash_transactions_to_beancount(self, output_file):
        """Export only cash transactions to Beancount format"""
        try:
            cash_transactions = self.get_cash_transactions()
            
            if cash_transactions.empty:
                print("No cash transactions found!")
                return
            
            # Collect all unique accounts
            unique_accounts = set()
            unique_accounts.add(self.sales_account)
            unique_accounts.add(self.vat_account)
            unique_accounts.add(self.cash_account)
            
            # Process cash transaction data
            transaction_data = []
            for _, row in cash_transactions.iterrows():
                organization = self.clean_organization_name(row['organization'])
                customer_sales_account = f"{self.sales_account}:{organization}"
                customer_vat_account = f"{self.vat_account}:{organization}"
                
                # Add customer-specific accounts
                unique_accounts.add(customer_sales_account)
                unique_accounts.add(customer_vat_account)
                
                # Calculate VAT breakdown
                total_amount = self.clean_amount(row['amount'])
                net_amount, vat_amount = self.calculate_vat_amounts(total_amount)
                
                # Store transaction data
                transaction_data.append({
                    'date': self.format_date(row['date']),
                    'amount': total_amount,
                    'net_amount': net_amount,
                    'vat_amount': vat_amount,
                    'organization': organization,
                    'customer_sales_account': customer_sales_account,
                    'customer_vat_account': customer_vat_account,
                    'payment_method': row['payment_method']
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header comment
                f.write(f";; Cash Transactions from Excel file: {self.excel_file_path}\n")
                f.write(f";; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f";; Contains only transactions paid in cash (ნაღდი)\n\n")
                
                # Write account opening directives
                for account in sorted(unique_accounts):
                    f.write(f"2021-01-01 open {account} {self.default_currency}\n")
                
                f.write("\n")  # Empty line after account definitions
                
                # Write cash transactions
                for tx in transaction_data:
                    f.write(f"{tx['date']} * \"Cash sale to {tx['organization']}\"\n")
                    f.write(f"    {self.cash_account}  {tx['amount']:.2f} {self.default_currency}\n")
                    f.write(f"    {tx['customer_sales_account']}  -{tx['net_amount']:.2f} {self.default_currency}\n")
                    f.write(f"    {tx['customer_vat_account']}  -{tx['vat_amount']:.2f} {self.default_currency}\n\n")

            print(f"Exported {len(transaction_data)} cash transactions to {output_file}")
            
            # Print summary
            total_cash_amount = sum(tx['amount'] for tx in transaction_data)
            print(f"Total cash received: {total_cash_amount:.2f} {self.default_currency}")
            
        except Exception as e:
            print(f"Error exporting cash transactions to Beancount file: {e}")
    
    def export_all_transactions_with_classification(self, output_file):
        """Export all transactions with proper cash vs receivables classification"""
        try:
            if self.df is None or self.df.empty:
                print("No transaction data available!")
                return
            
            # Collect all unique accounts
            unique_accounts = set()
            unique_accounts.add(self.sales_account)
            unique_accounts.add(self.vat_account)
            unique_accounts.add(self.cash_account)
            unique_accounts.add(self.receivables_account)
            
            # Process all transaction data
            transaction_data = []
            for _, row in self.df.iterrows():
                organization = self.clean_organization_name(row['organization'])
                customer_sales_account = f"{self.sales_account}:{organization}"
                customer_vat_account = f"{self.vat_account}:{organization}"
                customer_receivables_account = f"{self.receivables_account}:{organization}"
                
                # Add customer-specific accounts
                unique_accounts.add(customer_sales_account)
                unique_accounts.add(customer_vat_account)
                unique_accounts.add(customer_receivables_account)
                
                # Calculate VAT breakdown
                total_amount = self.clean_amount(row['amount'])
                net_amount, vat_amount = self.calculate_vat_amounts(total_amount)
                
                # Determine asset account based on payment method
                is_cash = row['is_cash_payment']
                asset_account = self.cash_account if is_cash else customer_receivables_account
                transaction_type = "Cash sale" if is_cash else "Credit sale"
                
                # Store transaction data
                transaction_data.append({
                    'date': self.format_date(row['date']),
                    'amount': total_amount,
                    'net_amount': net_amount,
                    'vat_amount': vat_amount,
                    'organization': organization,
                    'customer_sales_account': customer_sales_account,
                    'customer_vat_account': customer_vat_account,
                    'asset_account': asset_account,
                    'transaction_type': transaction_type,
                    'is_cash': is_cash,
                    'payment_method': row['payment_method']
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header comment
                f.write(f";; All Sales Transactions from Excel file: {self.excel_file_path}\n")
                f.write(f";; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f";; Cash sales go to Assets:Cash, credit sales go to Assets:Receivables\n\n")
                
                # Write account opening directives
                for account in sorted(unique_accounts):
                    f.write(f"2021-01-01 open {account} {self.default_currency}\n")
                
                f.write("\n")  # Empty line after account definitions
                
                # Write all transactions with proper classification
                for tx in transaction_data:
                    f.write(f"{tx['date']} * \"{tx['transaction_type']} to {tx['organization']}\"\n")
                    f.write(f"    {tx['asset_account']}  {tx['amount']:.2f} {self.default_currency}\n")
                    f.write(f"    {tx['customer_sales_account']}  -{tx['net_amount']:.2f} {self.default_currency}\n")
                    f.write(f"    {tx['customer_vat_account']}  -{tx['vat_amount']:.2f} {self.default_currency}\n\n")

            # Print detailed summary
            cash_transactions = [tx for tx in transaction_data if tx['is_cash']]
            credit_transactions = [tx for tx in transaction_data if not tx['is_cash']]
            
            print(f"Exported {len(transaction_data)} total transactions to {output_file}")
            print(f"  - {len(cash_transactions)} cash transactions")
            print(f"  - {len(credit_transactions)} credit transactions (receivables)")
            
            if cash_transactions:
                total_cash = sum(tx['amount'] for tx in cash_transactions)
                print(f"Total cash received: {total_cash:.2f} {self.default_currency}")
            
            if credit_transactions:
                total_receivables = sum(tx['amount'] for tx in credit_transactions)
                print(f"Total receivables created: {total_receivables:.2f} {self.default_currency}")
            
        except Exception as e:
            print(f"Error exporting transactions to Beancount file: {e}")
    
    def print_cash_payment_analysis(self):
        """Print detailed analysis of cash payments found"""
        if self.df is None:
            print("No data loaded!")
            return
        
        cash_transactions = self.get_cash_transactions()
        
        print("\n=== CASH PAYMENT ANALYSIS ===")
        print(f"Total transactions: {len(self.df)}")
        print(f"Cash transactions: {len(cash_transactions)}")
        print(f"Credit transactions: {len(self.df) - len(cash_transactions)}")
        
        if not cash_transactions.empty:
            print(f"\nCash payment indicators found:")
            payment_methods = cash_transactions['payment_method'].value_counts()
            for method, count in payment_methods.items():
                print(f"  '{method}': {count} transactions")
            
            total_cash_amount = cash_transactions['amount'].sum()
            print(f"\nTotal cash amount: {total_cash_amount:.2f} {self.default_currency}")
            
            print(f"\nSample cash transactions:")
            for i, (_, row) in enumerate(cash_transactions.head(5).iterrows()):
                print(f"  {i+1}. {row['organization']} - {row['amount']:.2f} {self.default_currency} - '{row['payment_method']}'")


def main():
    """Main function to run the cash payment detector"""
    if len(sys.argv) < 2:
        print("Usage: python cash_payment_detector.py <excel_file> [output_file]")
        print("Example: python cash_payment_detector.py report(18).xls cash_transactions.beancount")
        return
    
    excel_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'cash_transactions.beancount'
    
    detector = CashPaymentDetector(excel_file)
    
    if detector.load_data():
        # Print analysis
        detector.print_cash_payment_analysis()
        
        # Export transactions
        print(f"\nExporting all transactions with cash/credit classification to: {output_file}")
        detector.export_all_transactions_with_classification(output_file)
        
        # Also create cash-only file
        cash_only_file = output_file.replace('.beancount', '_cash_only.beancount')
        print(f"Exporting cash-only transactions to: {cash_only_file}")
        detector.export_cash_transactions_to_beancount(cash_only_file)
        
    else:
        print("Failed to load Excel data")


if __name__ == "__main__":
    # Default execution for report(18).xls
    excel_file_path = "report(18).xls"
    
    detector = CashPaymentDetector(excel_file_path)
    
    if detector.load_data():
        print("Data loaded successfully. Analyzing cash payments...")
        detector.print_cash_payment_analysis()
        
        # Export classified transactions
        detector.export_all_transactions_with_classification("sales_with_cash_classification.beancount")
        
        # Export cash-only transactions
        detector.export_cash_transactions_to_beancount("cash_sales_only.beancount")
    else:
        print("Failed to load data from the Excel file.")