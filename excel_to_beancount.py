#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel to Beancount Importer
Converts Georgian Excel financial data to Beancount format
"""

import pandas as pd
import sys
from datetime import datetime
import re


class ExcelToBeancountImporter:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.df = None
        
        # Column mappings for SALES data (only the 4 needed columns)
        self.column_map = {
            'ორგანიზაცია': 'organization',      # Customer/Organization
            'თანხა': 'amount',                  # Amount (VAT included)
            'გააქტიურების თარ.': 'date',         # Sale Date
            'შენიშვნა': 'payment_method',       # Payment method (cash/bank)
        }
        
        # Sales accounts structure
        self.sales_account = "Income:Sales"
        self.vat_account = "Liabilities:VAT:Output"
        self.cash_account = "Assets:Cash"
        self.bank_account = "Assets:Bank:Checking"
        
        # VAT rate (18%)
        self.vat_rate = 0.18
        
        # Default currency
        self.default_currency = "INR"  # Based on your existing ledger
        
    def load_data(self):
        """Load Excel data with proper encoding handling"""
        try:
            self.df = pd.read_excel(self.excel_file_path, engine='xlrd')
            print(f"Successfully loaded {len(self.df)} rows from Excel file")
            
            # Keep only the 4 columns we need for sales data
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
            
            print(f"Processed {len(self.df)} valid sales transactions")
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
    
    def determine_payment_account(self, payment_method):
        """Determine asset account based on payment method"""
        if pd.isna(payment_method):
            return self.bank_account  # Default to bank
        
        payment_str = str(payment_method).lower()
        
        # Check for cash indicators
        if any(word in payment_str for word in ['cash', 'ნაღდი', 'ნაღ', 'კეში']):
            return self.cash_account
        # Check for bank indicators  
        elif any(word in payment_str for word in ['bank', 'ბანკი', 'transfer', 'card', 'ბარათი']):
            return self.bank_account
        else:
            # If unclear, default to bank
            return self.bank_account
    
    def calculate_vat_amounts(self, total_amount):
        """Calculate VAT and net amounts from VAT-inclusive total"""
        # Total = Net + VAT
        # VAT = Net * VAT_rate
        # Total = Net + (Net * VAT_rate) = Net * (1 + VAT_rate)
        # Therefore: Net = Total / (1 + VAT_rate)
        
        net_amount = total_amount / (1 + self.vat_rate)
        vat_amount = total_amount - net_amount
        
        return net_amount, vat_amount
    
    def create_beancount_entry(self, row):
        """Create a single Beancount sales transaction entry"""
        date = self.format_date(row.get('date'))
        organization = str(row.get('organization', 'Unknown Customer')).strip()
        total_amount = self.clean_amount(row.get('amount', 0))
        payment_method = row.get('payment_method', '')
        
        if total_amount == 0:
            return None  # Skip zero-value transactions
        
        # Clean organization name for description
        organization = organization.replace('"', '\\"')  # Escape quotes
        
        # Determine payment account (cash vs bank)
        asset_account = self.determine_payment_account(payment_method)
        
        # Calculate VAT components
        net_amount, vat_amount = self.calculate_vat_amounts(total_amount)
        
        entry_lines = []
        entry_lines.append(f'{date} * "Sale to {organization}"')
        
        # Sales transaction structure:
        # Asset account receives the total amount
        entry_lines.append(f'    {asset_account}    {total_amount:.2f} {self.default_currency}')
        
        # Sales revenue (net amount without VAT)
        entry_lines.append(f'    {self.sales_account}    {-net_amount:.2f} {self.default_currency}')
        
        # VAT liability (VAT amount)
        entry_lines.append(f'    {self.vat_account}    {-vat_amount:.2f} {self.default_currency}')
        
        return '\n'.join(entry_lines) + '\n'
    
    def generate_account_declarations(self):
        """Generate account open declarations for sales operations"""
        accounts = set()
        
        # Always add these core sales accounts
        accounts.add(self.sales_account)
        accounts.add(self.vat_account)
        accounts.add(self.bank_account)
        accounts.add(self.cash_account)
        
        declarations = []
        for account in sorted(accounts):
            declarations.append(f'2025-01-01 open {account} {self.default_currency}')
        
        return '\n'.join(declarations) + '\n\n'
    
    def convert_to_beancount(self, output_file=None):
        """Convert the entire Excel file to Beancount format"""
        if self.df is None:
            print("No data loaded. Call load_data() first.")
            return False
        
        output_lines = []
        
        # Add header comment
        output_lines.append(';; Generated from Excel file: ' + self.excel_file_path)
        output_lines.append(';; Generated on: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        output_lines.append('')
        
        # Add account declarations
        output_lines.append(self.generate_account_declarations())
        
        # Convert each row to a Beancount entry
        successful_conversions = 0
        for index, row in self.df.iterrows():
            try:
                entry = self.create_beancount_entry(row)
                if entry:
                    output_lines.append(entry)
                    successful_conversions += 1
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                continue
        
        # Write to file or return as string
        result = '\n'.join(output_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Successfully converted {successful_conversions} transactions to {output_file}")
        
        return result


def main():
    """Main function to run the importer"""
    if len(sys.argv) < 2:
        print("Usage: python excel_to_beancount.py <excel_file> [output_file]")
        print("Example: python excel_to_beancount.py report(18).xls imported_transactions.beancount")
        return
    
    excel_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'imported_transactions.beancount'
    
    importer = ExcelToBeancountImporter(excel_file)
    
    if importer.load_data():
        result = importer.convert_to_beancount(output_file)
        if result:
            print(f"Conversion completed. Output saved to: {output_file}")
            print("\nFirst few lines of output:")
            print('\n'.join(result.split('\n')[:20]))
    else:
        print("Failed to load Excel data")


if __name__ == "__main__":
    main()