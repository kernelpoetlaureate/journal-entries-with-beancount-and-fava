import pandas as pd
import sys
import traceback

def analyze_excel_file(file_path):
    """Analyze the excel file to get the total amount"""
    try:
        # Load Excel file
        df = pd.read_excel(file_path, engine='openpyxl')
        print(f"Total rows in Excel: {len(df)}")
        
        # Get column names
        columns = list(df.columns)
        
        # Find the incoming amount column (column 4)
        amount_col = columns[4]  # "შემოსული თანხა"
        customer_col = columns[10]  # "პარტნიორი"
        
        # Convert amount column to numeric, forcing errors to NaN
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        
        # Basic statistics
        total_incoming = df[amount_col].sum()
        print(f"Total incoming amount: {total_incoming:,.2f}")
        
        # Count transactions with positive amounts
        positive_amount_count = (df[amount_col] > 0).sum()
        print(f"Transactions with positive amounts: {positive_amount_count}")
        
        # Filter to just rows with customer and amount
        valid_rows = df.dropna(subset=[customer_col, amount_col])
        valid_rows = valid_rows[valid_rows[amount_col] > 0]
        print(f"Valid rows with customer and positive amount: {len(valid_rows)}")
        
        # Sum of valid transactions
        valid_total = valid_rows[amount_col].sum()
        print(f"Sum of valid transactions: {valid_total:,.2f}")
        
        # Sample data
        print("\nSample of first few rows with amounts:")
        sample = valid_rows[[columns[0], amount_col, customer_col]].head(5)
        print(sample)
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    analyze_excel_file("tbc.xlsx")