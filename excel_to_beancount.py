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
        
        # Column mappings (Georgian to English)
        self.column_map = {
            'ზედნადები': 'description',          # Description/Narration
            'სტატუსი': 'status',                # Status
            'მდგომარეობა': 'state',              # State/Condition
            'კატეგორია': 'category',            # Category
            'ტიპი': 'type',                     # Type
            'ორგანიზაცია': 'organization',      # Organization
            'თანხა': 'amount',                  # Amount
            'მიწოდების ადგილი': 'location',       # Delivery Location
            'გააქტიურების თარ.': 'date',         # Activation Date
            'შენიშვნა': 'notes',                # Notes
            'ა/ფ ID': 'person_id',              # Person ID
            'STAT': 'stat',                     # Stat
            'ტრანსპორტირების ხარჯი': 'transport_cost',  # Transport Cost
            'ID': 'id'                          # ID
        }
        
        # Category to account mapping
        self.category_accounts = {
            # Default mappings - can be customized based on actual categories
            'default': 'Expenses:Miscellaneous',
            'transport': 'Expenses:Transport',
            'food': 'Expenses:Food', 
            'salary': 'Income:Salary',
            'refund': 'Income:Refunds'
        }
        
        # Default accounts
        self.default_asset_account = "Assets:Bank:Checking"
        self.default_currency = "INR"  # Based on your existing ledger
        
    def load_data(self):
        """Load Excel data with proper encoding handling"""
        try:
            self.df = pd.read_excel(self.excel_file_path, engine='xlrd')
            print(f"Successfully loaded {len(self.df)} rows from Excel file")
            
            # Rename columns to English for easier processing
            self.df = self.df.rename(columns=self.column_map)
            
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
    
    def categorize_transaction(self, row):
        """Determine the appropriate expense/income account based on category/description"""
        category = str(row.get('category', '')).lower()
        description = str(row.get('description', '')).lower()
        
        # Simple keyword-based categorization
        if any(word in category or word in description for word in ['transport', 'ტრანსპორტ', 'car', 'taxi']):
            return 'Expenses:Transport'
        elif any(word in category or word in description for word in ['food', 'საკვები', 'restaurant', 'lunch']):
            return 'Expenses:Food'
        elif any(word in category or word in description for word in ['salary', 'ხელფასი', 'income']):
            return 'Income:Salary'
        elif any(word in category or word in description for word in ['refund', 'დაბრუნება']):
            return 'Income:Refunds'
        else:
            return 'Expenses:Miscellaneous'
    
    def create_beancount_entry(self, row):
        """Create a single Beancount transaction entry"""
        date = self.format_date(row.get('date'))
        description = str(row.get('description', 'Unknown transaction')).strip()
        amount = self.clean_amount(row.get('amount', 0))
        transport_cost = self.clean_amount(row.get('transport_cost', 0))
        
        if amount == 0 and transport_cost == 0:
            return None  # Skip zero-value transactions
        
        # Clean description for Beancount format
        description = description.replace('"', '\\"')  # Escape quotes
        
        # Determine account based on category
        counter_account = self.categorize_transaction(row)
        
        entry_lines = []
        entry_lines.append(f'{date} * "{description}"')
        
        # Main amount posting
        if amount != 0:
            if counter_account.startswith('Income:'):
                # Income transaction: positive to asset, negative from income
                entry_lines.append(f'    {self.default_asset_account}    {amount:.2f} {self.default_currency}')
                entry_lines.append(f'    {counter_account}')  # Let Beancount interpolate
            else:
                # Expense transaction: negative from asset, positive to expense
                entry_lines.append(f'    {self.default_asset_account}    {-amount:.2f} {self.default_currency}')
                entry_lines.append(f'    {counter_account}')  # Let Beancount interpolate
        
        # Add transport cost if present
        if transport_cost != 0:
            entry_lines.append(f'    {self.default_asset_account}    {-transport_cost:.2f} {self.default_currency}')
            entry_lines.append(f'    Expenses:Transport')
        
        return '\n'.join(entry_lines) + '\n'
    
    def generate_account_declarations(self):
        """Generate account open declarations"""
        accounts = set()
        accounts.add(self.default_asset_account)
        
        # Collect all accounts used
        for _, row in self.df.iterrows():
            account = self.categorize_transaction(row)
            accounts.add(account)
        
        # Add transport account if transport costs exist
        if self.df['transport_cost'].notna().any():
            accounts.add('Expenses:Transport')
        
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