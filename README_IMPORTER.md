# Excel to Beancount Importer - Usage Guide

## Overview
Successfully created a Python importer that converts your Georgian Excel financial data (`report(18).xls`) to Beancount format.

## What Was Accomplished

### 1. Data Analysis
- Successfully read 247 transactions from `report(18).xls`
- Identified column structure with Georgian headers
- Mapped columns to financial data (amounts, dates, descriptions, etc.)

### 2. Generated Output
- **File**: `imported_transactions.beancount`
- **Transactions**: 247 entries
- **Postings**: 494 (2 per transaction)
- **Date Range**: 2025-08-21 to 2025-09-22
- **Total Volume**: 67,913.00 INR

### 3. Account Structure
The importer automatically created these accounts:
- `Assets:Bank:Checking` (main bank account)
- `Expenses:Miscellaneous` (default expense category)
- `Expenses:Transport` (for transport costs)

## Files Created

### 1. `excel_to_beancount.py`
Main importer script with features:
- Handles Georgian text encoding
- Maps Excel columns to Beancount fields
- Converts dates to YYYY-MM-DD format
- Creates balanced double-entry transactions
- Supports transport cost allocation

### 2. `imported_transactions.beancount`
Generated Beancount file containing all transactions in proper format.

### 3. Validation Scripts
- `validate_beancount.py` - Basic format validation
- `analyze_import.py` - Detailed statistics

## Usage

### Basic Import
```bash
python excel_to_beancount.py "report(18).xls" output_file.beancount
```

### Analyze Results
```bash
python analyze_import.py
```

## Customization Options

### 1. Account Mapping
Edit the `category_accounts` dictionary in `excel_to_beancount.py`:
```python
self.category_accounts = {
    'transport': 'Expenses:Transport',
    'food': 'Expenses:Food',
    'salary': 'Income:Salary',
    # Add your custom mappings
}
```

### 2. Currency
Change the default currency by modifying:
```python
self.default_currency = "INR"  # Change to USD, EUR, etc.
```

### 3. Default Account
Modify the asset account:
```python
self.default_asset_account = "Assets:Bank:Checking"
```

## Transaction Format
Each transaction follows this structure:
```
2025-09-22 * "927939183"
    Assets:Bank:Checking    -200.00 INR
    Expenses:Miscellaneous
```

## Integration with Your Ledger

### Option 1: Append to Existing Ledger
```bash
cat imported_transactions.beancount >> my-ledger.beancount
```

### Option 2: Manual Review and Copy
1. Open `imported_transactions.beancount`
2. Review transactions for accuracy
3. Copy relevant entries to your main ledger
4. Adjust categories as needed

## Next Steps

### 1. Category Enhancement
Consider adding more specific category mappings based on transaction descriptions or amounts.

### 2. Duplicate Detection
Before importing, check for duplicates with your existing transactions.

### 3. Account Reconciliation
Verify the total amounts match your bank statements.

### 4. Regular Imports
Use this script regularly for new Excel exports from your financial system.

## Validation
The generated file is properly formatted Beancount syntax with:
- Proper date formats (YYYY-MM-DD)
- Balanced double-entry transactions
- Correct account hierarchies
- Appropriate currency declarations

## Troubleshooting

### Encoding Issues
If you encounter Georgian text encoding problems, ensure:
- Files are saved as UTF-8
- Python environment supports Unicode
- Console/terminal supports Unicode output

### Date Format Issues
The script handles multiple date formats, but you can customize the `format_date()` function for specific formats.

### Amount Parsing
The script handles various number formats, but verify amounts are correctly parsed for your specific data format.