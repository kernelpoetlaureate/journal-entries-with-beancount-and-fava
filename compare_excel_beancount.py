import pandas as pd
from decimal import Decimal
import re

def compare_excel_to_beancount():
    """Compare the Excel file to the Beancount file to identify discrepancies"""
    # 1. Analyze Excel file
    excel_file = "tbc.xlsx"
    df = pd.read_excel(excel_file, engine='openpyxl')
    
    # Get the amount column (column 4 based on previous output)
    amount_col = df.columns[4]  # "შემოსული თანხა"
    
    # Convert to numeric and calculate sum
    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
    excel_sum = Decimal(str(df[amount_col].sum()))  # Convert to Decimal for consistent comparison
    excel_count = (df[amount_col] > 0).sum()
    
    print(f"Excel Analysis:")
    print(f"Total rows: {len(df)}")
    print(f"Rows with positive amounts: {excel_count}")
    print(f"Sum of all amounts: {excel_sum:,.2f}")
    
    # 2. Analyze Beancount file
    beancount_file = "tbc_payments.beancount"
    tbc_account = "Assets:Bank:Checking:TBC"
    
    # Extract TBC account entries
    tbc_amounts = []
    transaction_count = 0
    
    with open(beancount_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Count transactions
            if line and line[0].isdigit() and ' * ' in line:
                transaction_count += 1
                
            # Extract TBC account lines
            elif line.startswith(tbc_account):
                parts = line.split()
                if len(parts) >= 3 and parts[2] == "GEL":
                    try:
                        amount = Decimal(parts[1])
                        tbc_amounts.append(amount)
                    except (ValueError, IndexError):
                        pass
    
    beancount_sum = sum(tbc_amounts)
    
    print(f"\nBeancount Analysis:")
    print(f"Total transactions: {transaction_count}")
    print(f"TBC account entries: {len(tbc_amounts)}")
    print(f"Sum of TBC account: {beancount_sum:,.2f}")
    
    # 3. Compare the two
    print(f"\nComparison:")
    print(f"Excel sum: {excel_sum:,.2f}")
    print(f"Beancount TBC sum: {beancount_sum:,.2f}")
    print(f"Difference: {abs(excel_sum - beancount_sum):,.2f}")
    
    # Safely calculate percentage difference
    if excel_sum != 0:
        pct_diff = abs(excel_sum - beancount_sum) / excel_sum * 100
        print(f"Percent difference: {pct_diff:.2f}%")
    
    if abs(excel_sum - beancount_sum) < Decimal('0.01'):
        print("The amounts match closely.")
    else:
        print("There is a difference between the Excel and Beancount amounts.")
        
        # Check for possible explanations
        if len(tbc_amounts) != excel_count:
            print(f"Transaction count mismatch: Excel has {excel_count} positive amounts, Beancount has {len(tbc_amounts)} TBC entries")
            
        # Check if there might be duplicated transactions
        if len(tbc_amounts) > excel_count:
            print(f"Beancount file may contain {len(tbc_amounts) - excel_count} duplicate or extra transactions")
            
        elif len(tbc_amounts) < excel_count:
            print(f"Beancount file may be missing {excel_count - len(tbc_amounts)} transactions from the Excel file")
            
        # Analyze the distribution of amounts
        from collections import Counter
        amount_counts = Counter(tbc_amounts)
        duplicates = {amount: count for amount, count in amount_counts.items() if count > 1}
        if duplicates:
            print(f"Found {len(duplicates)} amounts that appear multiple times in the Beancount file")
            
            # Show the top 5 most duplicated amounts
            most_common = sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]
            for amount, count in most_common:
                print(f"  Amount {amount} appears {count} times")

if __name__ == "__main__":
    compare_excel_to_beancount()