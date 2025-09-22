#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TBC Bank Payments to Beancount Importer
Converts Georgian TBC bank payment data to Beancount format
Handles customer payments that reduce receivables
"""

import pandas as pd
import sys
from datetime import datetime
import re


class TBCPaymentsImporter:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.df = None
        
        # Column mappings for TBC payment data
        self.column_map = {
            'თარიღი': 'date',                          # Payment date
            'შემოსული თანხა': 'amount',                 # Amount received
            'პარტნიორი': 'customer',                    # Customer name (column 10)
            'გადასახადის გადამხდელის კოდი': 'tax_code'   # Customer tax code (column 17)
        }
        
        # Bank account for TBC payments
        self.tbc_bank_account = "Assets:Bank:Checking:TBC"
        
        # Default currency
        self.default_currency = "GEL"  # Georgian Lari
        
    def load_data(self):
        """Load Excel data with proper encoding handling"""
        try:
            self.df = pd.read_excel(self.excel_file_path, engine='openpyxl')
            print(f"Successfully loaded {len(self.df)} rows from TBC Excel file")
            
            # Print all available columns for debugging
            print("Available columns:")
            for i, col in enumerate(self.df.columns):
                print(f"  {i}: {col}")
            
            # Keep only the 4 columns we need for payment data
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
            self.df = self.df.dropna(subset=['customer', 'amount'])
            
            # Clean amounts first, then filter out zero or negative amounts
            self.df['amount'] = self.df['amount'].apply(self.clean_amount)
            self.df = self.df[self.df['amount'] > 0]
            
            print(f"Processed {len(self.df)} valid payment transactions")
            return True
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            return False
    
    def clean_amount(self, amount):
        """Clean and convert amount to float"""
        if pd.isna(amount):
            return 0.0
        
        # Handle various amount formats
        if isinstance(amount, str):
            # Remove any non-numeric characters except decimal point and minus
            cleaned = re.sub(r'[^\d.-]', '', str(amount))
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        
        return float(amount)
    
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
    
    def clean_customer_name(self, customer_name):
        """Clean customer name to create valid Beancount account names"""
        if pd.isna(customer_name):
            return "Unknown"
        
        # Convert to string and clean
        clean_name = str(customer_name).strip()
        
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
    
    def get_receivables_account(self, customer_name, tax_code=None):
        """Generate receivables account name for customer"""
        clean_customer = self.clean_customer_name(customer_name)
        
        # If we have tax code, include it for better identification
        if pd.notna(tax_code) and str(tax_code).strip():
            clean_tax_code = re.sub(r'[^\w\-]', '', str(tax_code).strip())
            if clean_tax_code:
                clean_customer = f"{clean_tax_code}-{clean_customer}"
        
        return f"Assets:Receivables:{clean_customer}"
    
    def export_to_beancount(self, output_file):
        """Export processed payment data to a Beancount file with proper account definitions"""
        try:
            # Collect all unique accounts that will be used
            unique_accounts = set()
            unique_accounts.add(self.tbc_bank_account)
            
            # Process data to collect customer receivables accounts
            transaction_data = []
            for _, row in self.df.iterrows():
                customer_name = row['customer']
                tax_code = row.get('tax_code', None)
                receivables_account = self.get_receivables_account(customer_name, tax_code)
                
                # Add accounts to unique set
                unique_accounts.add(receivables_account)
                
                # Store transaction data
                transaction_data.append({
                    'date': self.format_date(row['date']),
                    'amount': self.clean_amount(row['amount']),
                    'customer': self.clean_customer_name(customer_name),
                    'receivables_account': receivables_account,
                    'tax_code': tax_code
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header comment
                f.write(f";; Generated from TBC Excel file: {self.excel_file_path}\n")
                f.write(f";; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f";; Payment transactions that reduce customer receivables\n\n")
                
                # Write account opening directives
                for account in sorted(unique_accounts):
                    f.write(f"2021-01-01 open {account} {self.default_currency}\n")
                
                f.write("\n")  # Empty line after account definitions
                
                # Write transactions
                for tx in transaction_data:
                    tax_code_info = f" (Tax Code: {tx['tax_code']})" if pd.notna(tx['tax_code']) else ""
                    f.write(f"{tx['date']} * \"Payment received from {tx['customer']}{tax_code_info}\"\n")
                    f.write(f"    {self.tbc_bank_account}  {tx['amount']:.2f} {self.default_currency}\n")
                    f.write(f"    {tx['receivables_account']}  -{tx['amount']:.2f} {self.default_currency}\n\n")

            print(f"Exported {len(transaction_data)} payment transactions with account definitions to {output_file}")
        except Exception as e:
            print(f"Error exporting to Beancount file: {e}")


if __name__ == "__main__":
    # Path to the TBC payments .xlsx file
    excel_file_path = "tbc.xlsx"

    # Initialize the importer with the file path
    importer = TBCPaymentsImporter(excel_file_path)

    # Load and process the data
    if importer.load_data():
        print("TBC payment data loaded successfully. Proceeding with export.")
        # Export to Beancount file
        importer.export_to_beancount("tbc_payments.beancount")
    else:
        print("Failed to load data from the TBC Excel file.")