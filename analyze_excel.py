import pandas as pd
import sys

def analyze_excel_file(file_path):
    """Analyze the excel file to get the total amount"""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        print(f"Total rows in Excel: {len(df)}")
        
        # Print all column names
        print("\nColumns in Excel file:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
        
        # Try to find the amount column by index (column 4 based on the previous output)
        amount_column = df.columns[4]  # "შემოსული თანხა" (incoming amount)
        
        # Calculate sum of amounts
        sum_amount = df[amount_column].sum()
        print(f"\nAmount column found: {amount_column}")
        print(f"Sum of amounts: {sum_amount:.2f}")
        
        # Count of non-zero amounts
        non_zero_count = df[amount_column].dropna().astype(float).gt(0).sum()
        print(f"Count of non-zero amounts: {non_zero_count}")
        
        # Count rows before and after cleaning as done in the importer
        customer_column = df.columns[10]  # "პარტნიორი" (customer/partner)
        date_column = df.columns[0]  # "თარიღი" (date)
        tax_code_column = df.columns[17]  # "გადასახადის გადამხდელის კოდი" (tax code)
        
        # First drop NaN in key columns
        print(f"\nCleaning process:")
        print(f"Original rows: {len(df)}")
        
        # Convert amounts to numeric, handling errors
        df[amount_column] = pd.to_numeric(df[amount_column], errors='coerce')
        
        # Drop rows with NaN in critical columns
        cleaned_df = df.dropna(subset=[customer_column, amount_column])
        print(f"Rows after removing NaN values: {len(cleaned_df)}")
        
        # Filter positive amounts only
        positive_df = cleaned_df[cleaned_df[amount_column] > 0]
        print(f"Rows with positive amounts: {len(positive_df)}")
        
        # Check for duplicate rows
        duplicate_subset = [date_column, amount_column, customer_column]
        if tax_code_column in df.columns:
            duplicate_subset.append(tax_code_column)
            
        duplicates = positive_df.duplicated(subset=duplicate_subset, keep='first')
        duplicate_count = duplicates.sum()
        print(f"Duplicate rows (same date, amount, customer, tax code): {duplicate_count}")
        
        # Final count after deduplication
        final_df = positive_df[~duplicates]
        print(f"Final rows after deduplication: {len(final_df)}")
        
        # Calculate final sum
        final_sum = final_df[amount_column].sum()
        print(f"Final sum after cleaning: {final_sum:.2f}")
        
    except Exception as e:
        import traceback
        print(f"Error analyzing Excel file: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    analyze_excel_file("tbc.xlsx")