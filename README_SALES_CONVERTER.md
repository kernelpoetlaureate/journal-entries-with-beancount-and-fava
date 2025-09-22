# Excel to Beancount Sales Converter

A specialized tool for converting Georgian Excel sales reports to Beancount format with customer-specific sub-accounts, VAT handling, and payment method detection.

## 🎯 Overview

This converter transforms Excel sales data into properly structured Beancount transactions with:
- **Customer-specific sub-accounts** for detailed tracking
- **Automatic VAT calculation** (18% included in amounts)
- **Payment method detection** (cash vs bank)
- **Georgian language support** for organization names
- **Double-entry bookkeeping** compliance

## 📊 Input Data Format

### Required Excel Columns
Your Excel file must contain these **4 essential columns** (other columns are ignored):

| Georgian Column | English Translation | Purpose |
|---|---|---|
| `ორგანიზაცია` | Organization/Customer | Customer name and tax ID |
| `თანხა` | Amount | Total amount (VAT-inclusive) |
| `გააქტიურების თარ.` | Activation Date | Sale transaction date |
| `შენიშვნა` | Notes | Payment method indicator |

### Sample Excel Data
```
ორგანიზაცია                           | თანხა | გააქტიურების თარ. | შენიშვნა
(412764389-დღგ) შპს ფლორმარ კოსმეტიკს  | 200   | 2025-09-22       | bank
(60001009790-დღგ) კონსტანტინე ხელაძე   | 60    | 2025-09-22       | cash
```

## 🚀 Usage

### Basic Command
```bash
python excel_to_beancount.py <excel_file> [output_file]
```

### Examples
```bash
# Convert with automatic output filename
python excel_to_beancount.py report(18).xls

# Convert with custom output filename
python excel_to_beancount.py report(18).xls sales_transactions.beancount
```

### Output
- **Default output**: `imported_transactions.beancount`
- **Custom output**: As specified in command line

## 📁 Generated Account Structure

The converter creates customer-specific sub-accounts under each main category:

### Account Hierarchy
```
Assets:
  ├── Bank:
  │   └── Checking:
  │       ├── {CustomerName}     # Bank payments per customer
  │       └── {CustomerName}
  ├── Cash:
  │   ├── {CustomerName}         # Cash payments per customer
  │   └── {CustomerName}
  └── Receivables:               # For future receivables tracking
      ├── {CustomerName}
      └── {CustomerName}

Income:
  └── Sales:
      ├── {CustomerName}         # Revenue per customer
      └── {CustomerName}

Liabilities:
  └── VAT:
      └── Output:
          ├── {CustomerName}     # VAT liability per customer
          └── {CustomerName}
```

### Customer Name Cleaning Rules
Organization names are automatically cleaned for Beancount compatibility:
- Spaces → hyphens (`-`)
- Special characters removed
- Names starting with non-alphanumeric get `C` prefix
- Maximum 50 characters
- Georgian characters preserved

**Example**: `(412764389-დღგ) შპს ფლორმარ კოსმეტიკს` becomes `412764389-დღგ-შპს-ფლორმარ-კოსმეტიკს`

## 💰 Financial Logic

### VAT Calculation (18%)
All amounts in Excel are **VAT-inclusive**. The converter automatically splits them:

```
Total Amount = Net Sales + VAT
VAT = Net Sales × 18%
Net Sales = Total Amount ÷ 1.18
```

**Example**: 200 GEL total → 169.49 GEL net sales + 30.51 GEL VAT

### Payment Method Detection
The `შენიშვნა` column determines the asset account:

| Keywords in შენიშვნა | Asset Account |
|---|---|
| `cash`, `ნაღდი`, `ნაღ`, `კეში` | `Assets:Cash:{Customer}` |
| `bank`, `ბანკი`, `transfer`, `card`, `ბარათი` | `Assets:Bank:Checking:{Customer}` |
| *Default/unclear* | `Assets:Bank:Checking:{Customer}` |

### Transaction Structure
Each sale generates a three-line double-entry transaction:

```beancount
2025-09-22 * "Sale to (CustomerTaxID) Customer Name"
    Assets:Bank:Checking:Customer-Name    200.00 GEL  ; Total amount received
    Income:Sales:Customer-Name           -169.49 GEL  ; Net sales revenue
    Liabilities:VAT:Output:Customer-Name  -30.51 GEL  ; VAT owed to government
```

## 🔧 Setup and Dependencies

### Prerequisites
```bash
pip install pandas xlrd
```

### File Requirements
- **Python 3.6+**
- **Excel file** with `.xls` extension (xlrd engine)
- **4 required columns** as described above

## ✅ Validation

### Check Generated File
Always validate your generated Beancount file:

```bash
# Using beancount tools
python beancount/bin/bean-check sales_transactions.beancount

# Should return no errors if successful
```

### Common Issues and Solutions

#### Invalid Token Errors
**Problem**: Account names with underscores or starting with special characters
**Solution**: The converter automatically fixes these, but if you see errors:
- Check for unusual characters in organization names
- Ensure latest version of converter with hyphen-based naming

#### Missing Transactions
**Problem**: Zero transactions converted
**Solutions**:
- Verify Excel file has the 4 required columns
- Check for empty organization or amount fields
- Ensure Excel file uses `.xls` format (not `.xlsx`)

#### Encoding Issues
**Problem**: Georgian characters not displaying correctly
**Solution**: Ensure your terminal/editor supports UTF-8 encoding

## 📈 Using with Fava

### Start Fava Server
```bash
# In WSL/Linux terminal
fava sales_transactions.beancount

# Access at http://localhost:5000
```

### Useful Fava Views
1. **Balance Sheet**: See customer-wise asset balances
2. **Income Statement**: Revenue breakdown by customer
3. **Account Details**: Drill down into specific customer accounts
4. **Statistics**: Customer sales analysis

## 🎯 Best Practices

### Data Preparation
1. **Clean Excel data** before conversion:
   - Remove empty rows
   - Ensure consistent date formats
   - Verify amount fields contain only numbers

2. **Backup original files** before conversion

3. **Test with small dataset** first to verify output format

### Account Management
1. **Regular validation**: Run `bean-check` after each conversion
2. **Merge carefully**: When adding to existing ledger, check for account conflicts
3. **Monitor VAT totals**: Ensure VAT calculations match tax requirements

### Workflow Integration
1. **Separate files**: Keep sales transactions in separate files by period
2. **Include directive**: Use `include` statements in main ledger:
   ```beancount
   include "sales_september_2025.beancount"
   ```

## 📋 Example Complete Workflow

```bash
# 1. Convert Excel to Beancount
python excel_to_beancount.py monthly_sales.xls sales_sept_2025.beancount

# 2. Validate the output
python beancount/bin/bean-check sales_sept_2025.beancount

# 3. Add to main ledger (edit my-ledger.beancount)
echo 'include "sales_sept_2025.beancount"' >> my-ledger.beancount

# 4. Validate complete ledger
python beancount/bin/bean-check my-ledger.beancount

# 5. Start Fava for analysis
fava my-ledger.beancount
```

## 🛠️ Troubleshooting

### Converter Script Issues
```bash
# Check Python and dependencies
python --version
pip list | grep pandas

# Verify file paths (use absolute paths if needed)
python excel_to_beancount.py "C:/full/path/to/report.xls"
```

### Fava Issues
```bash
# Install/reinstall Fava
pipx install fava
pipx ensurepath
source ~/.bashrc

# Start with explicit port
fava -p 5001 my-ledger.beancount
```

## 📞 Support

If you encounter issues:
1. **Check this README** for common solutions
2. **Validate input data** format matches requirements
3. **Test with minimal dataset** to isolate problems
4. **Check Beancount syntax** with bean-check

---

## 📝 Technical Notes

- **Currency**: All amounts use Georgian Lari (GEL)
- **VAT Rate**: Fixed at 18% (configurable in script)
- **Date Format**: Automatic detection and conversion to YYYY-MM-DD
- **Encoding**: UTF-8 for Georgian character support
- **Account Naming**: Follows Beancount standards with hyphen separators

**Version**: 1.0  
**Last Updated**: September 2025  
**Compatibility**: Beancount 2.x, Fava 1.x