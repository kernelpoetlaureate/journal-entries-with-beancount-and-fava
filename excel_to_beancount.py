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
        self.default_currency = "GEL"  # Georgian Lari
        
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
    
    def clean_organization_name(self, org_name):
        """Clean organization name to create valid Beancount account names"""
        if pd.isna(org_name):
            return "Unknown"
        
        # Convert to string and clean
        clean_name = str(org_name).strip()
        
        # Replace problematic characters for account names
        # Keep Georgian characters, letters, numbers, and some symbols
        clean_name = re.sub(r'[^\w\s\-\(\)ა-ჰ]', '', clean_name)
        
        # Replace spaces and special characters with hyphens (not underscores)
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
    
    def get_customer_accounts(self, organization):
        """Generate customer-specific account names"""
        customer_name = self.clean_organization_name(organization)
        
        return {
            'bank': f"Assets:Bank:Checking:{customer_name}",
            'cash': f"Assets:Cash:{customer_name}",
            'sales': f"Income:Sales:{customer_name}",
            'vat': f"Liabilities:VAT:Output:{customer_name}",
            'receivables': f"Assets:Receivables:{customer_name}"
        }
    
    def determine_payment_account(self, payment_method, customer_accounts):
        """Determine asset account based on payment method"""
        if pd.isna(payment_method):
            return customer_accounts['bank']  # Default to bank
        
        payment_str = str(payment_method).lower()
        
        # Check for cash indicators
        if any(word in payment_str for word in ['cash', 'ნაღდი', 'ნაღ', 'კეში']):
            return customer_accounts['cash']
        # Check for bank indicators  
        elif any(word in payment_str for word in ['bank', 'ბანკი', 'transfer', 'card', 'ბარათი']):
            return customer_accounts['bank']
        else:
            # If unclear, default to bank
            return customer_accounts['bank']
    
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
        """Create a single Beancount sales transaction entry with customer sub-accounts"""
        date = self.format_date(row.get('date'))
        organization = str(row.get('organization', 'Unknown Customer')).strip()
        total_amount = self.clean_amount(row.get('amount', 0))
        payment_method = row.get('payment_method', '')
        
        if total_amount == 0:
            return None  # Skip zero-value transactions
        
        # Clean organization name for description
        organization_clean = organization.replace('"', '\\"')  # Escape quotes
        
        # Get customer-specific accounts
        customer_accounts = self.get_customer_accounts(organization)
        
        # Determine payment account (cash vs bank)
        asset_account = self.determine_payment_account(payment_method, customer_accounts)
        
        # Calculate VAT components
        net_amount, vat_amount = self.calculate_vat_amounts(total_amount)
        
        entry_lines = []
        entry_lines.append(f'{date} * "Sale to {organization_clean}"')
        
        # Sales transaction structure with customer sub-accounts:
        # Asset account (Bank/Cash) receives the total amount
        entry_lines.append(f'    {asset_account}    {total_amount:.2f} {self.default_currency}')
        
        # Sales revenue (net amount without VAT) - customer specific
        entry_lines.append(f'    {customer_accounts["sales"]}    {-net_amount:.2f} {self.default_currency}')
        
        # VAT liability (VAT amount) - customer specific
        entry_lines.append(f'    {customer_accounts["vat"]}    {-vat_amount:.2f} {self.default_currency}')
        
        return '\n'.join(entry_lines) + '\n'
    
    def generate_account_declarations(self):
        """Generate account open declarations for sales operations with customer sub-accounts"""
        accounts = set()
        
        # Collect all customer accounts
        for _, row in self.df.iterrows():
            organization = row.get('organization', 'Unknown Customer')
            customer_accounts = self.get_customer_accounts(organization)
            
            # Add all customer-specific accounts
            for account in customer_accounts.values():
                accounts.add(account)
        
        # Also add parent accounts for organizational clarity
        parent_accounts = [
            "Assets:Bank:Checking",
            "Assets:Cash", 
            "Assets:Receivables",
            "Income:Sales",
            "Liabilities:VAT:Output"
        ]
        
        for parent in parent_accounts:
            accounts.add(parent)
        
        declarations = []
        for account in sorted(accounts):
            # Ensure proper formatting - account name, space, currency, newline
            declarations.append(f'2021-01-01 open {account} {self.default_currency}')
        
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
    
    def export_to_beancount(self, output_file):
        """Export processed data to a Beancount file with proper account definitions"""
        try:
            # Collect all unique accounts that will be used
            unique_accounts = set()
            unique_accounts.add(self.sales_account)
            unique_accounts.add(self.vat_account)
            unique_accounts.add(self.cash_account)
            unique_accounts.add(self.bank_account)
            
            # Process data to collect customer accounts
            transaction_data = []
            for _, row in self.df.iterrows():
                organization = self.clean_organization_name(row['organization'])
                customer_accounts = self.get_customer_accounts(organization)
                payment_method = row.get('payment_method', 'bank')
                payment_account = self.determine_payment_account(payment_method, customer_accounts)
                
                # Add receivables account to unique set (this is what we'll actually use)
                receivables_account = f"Assets:Receivables:{organization}"
                unique_accounts.add(receivables_account)
                
                # Add other accounts to unique set for potential future use
                for account in customer_accounts.values():
                    unique_accounts.add(account)
                unique_accounts.add(payment_account)
                
                # Store transaction data
                transaction_data.append({
                    'date': self.format_date(row['date']),
                    'amount': self.clean_amount(row['amount']),
                    'organization': organization,
                    'payment_account': payment_account
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Write header comment
                f.write(f";; Generated from Excel file: {self.excel_file_path}\n")
                f.write(f";; Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write account opening directives
                for account in sorted(unique_accounts):
                    f.write(f"2021-01-01 open {account} {self.default_currency}\n")
                
                f.write("\n")  # Empty line after account definitions
                
                # Write transactions
                for tx in transaction_data:
                    # Create receivables account for customer
                    receivables_account = f"Assets:Receivables:{self.clean_organization_name(tx['organization'])}"
                    
                    # Calculate VAT components
                    total_amount = tx['amount']
                    net_sales = total_amount / (1 + self.vat_rate)  # Remove VAT from total
                    vat_amount = total_amount - net_sales           # VAT portion
                    
                    f.write(f"{tx['date']} * \"Sale to {tx['organization']}\"\n")
                    f.write(f"    {self.sales_account}  -{net_sales:.2f} {self.default_currency}\n")
                    f.write(f"    {self.vat_account}  -{vat_amount:.2f} {self.default_currency}\n")
                    f.write(f"    {receivables_account}  {total_amount:.2f} {self.default_currency}\n\n")

            print(f"Exported {len(transaction_data)} transactions with account definitions to {output_file}")
        except Exception as e:
            print(f"Error exporting to Beancount file: {e}")

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
    # Path to the new .xls file
    excel_file_path = "report(18).xls"

    # Initialize the importer with the file path
    importer = ExcelToBeancountImporter(excel_file_path)

    # Load and process the data
    if importer.load_data():
        print("Data loaded successfully. Proceeding with export.")
        # Export to Beancount file
        importer.export_to_beancount("imported_transactions.beancount")
    else:
        print("Failed to load data from the Excel file.")