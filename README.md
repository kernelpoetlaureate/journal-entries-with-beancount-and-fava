# Beancount Personal Finance Setup Guide

This guide helps you set up and use Beancount for personal finance tracking on Windows with WSL.

## 🚀 Quick Start

### First Time Setup (Run Once)
```bash
# In PowerShell
wsl
cd ~
chmod +x setup.sh
./setup.sh
```

### Daily Usage (Every Time)
```bash
# In PowerShell
wsl
cd ~
./start-beancount.sh
```

Or use the Windows batch file:
```cmd
start-beancount.bat
```

## 📋 What's Included

- **setup.sh** - One-time installation script
- **start-beancount.sh** - Daily startup script  
- **start-beancount.bat** - Windows batch file for easy access
- **my-ledger.beancount** - Your personal ledger file

## 🛠️ Manual Setup (if scripts don't work)

### 1. Install Dependencies
```bash
sudo apt update && sudo apt install -y build-essential python3 python3-venv python3-pip git meson ninja-build
```

### 2. Create Virtual Environment
```bash
cd ~
python3 -m venv beancount-env
source beancount-env/bin/activate
```

### 3. Install Build Tools
```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install meson-python meson ninja
```

### 4. Install Beancount
```bash
python -m pip install --no-build-isolation -e /mnt/c/Users/giorgi/Downloads/beancount/beancount
```

### 5. Install Fava (Web Interface)
```bash
pip install fava
```

## 📊 Using Beancount

### Validate Your Ledger
```bash
bean-check my-ledger.beancount
```

### Start Web Interface
```bash
fava my-ledger.beancount
```
Then open http://localhost:5000 in your browser.

### Format Your Ledger
```bash
bean-format my-ledger.beancount
```

## 📝 Ledger File Structure

Your `my-ledger.beancount` file should follow this structure:

```beancount
;; My Personal Ledger
option "title" "My Personal Finance"
option "operating_currency" "INR"

;; Open accounts (required before using)
2025-01-01 open Assets:Bank:Checking INR
2025-01-01 open Assets:Cash INR
2025-01-01 open Income:Salary INR
2025-01-01 open Expenses:Food INR
2025-01-01 open Expenses:Transport INR
2025-01-01 open Equity:Opening-Balances INR

;; Starting balance
2025-09-01 * "Opening balance"
  Assets:Bank:Checking    25000.00 INR
  Equity:Opening-Balances

;; Sample transactions
2025-09-22 * "Monthly salary"
  Assets:Bank:Checking   50000.00 INR
  Income:Salary

2025-09-22 * "Lunch"
  Expenses:Food    300.00 INR
  Assets:Cash
```

## 🏗️ Account Types

- **Assets**: Things you own (bank accounts, cash, investments)
- **Liabilities**: Things you owe (credit cards, loans)
- **Income**: Money coming in (salary, interest)
- **Expenses**: Money going out (food, transport, utilities)
- **Equity**: Net worth adjustments

## 🔧 Troubleshooting

### WSL Memory Issues
If you get "Insufficient system resources" error:

1. Create/edit `C:\Users\giorgi\.wslconfig`:
```ini
[wsl2]
memory=3GB
processors=2
```

2. Restart WSL:
```cmd
wsl --shutdown
wsl
```

### Virtual Environment Issues
If environment activation fails:
```bash
cd ~
rm -rf beancount-env
python3 -m venv beancount-env
source beancount-env/bin/activate
```

### Permission Issues
Make scripts executable:
```bash
chmod +x setup.sh
chmod +x start-beancount.sh
```

### Fava Won't Start
Check if port 5000 is busy:
```bash
fava my-ledger.beancount --port 5001
```

## 📂 File Locations

- **Ledger file**: `~/my-ledger.beancount` (in WSL)
- **Scripts**: `~/` (in WSL home directory)
- **Windows access**: Files are in `/mnt/c/Users/giorgi/` from WSL

## 🎯 Daily Workflow

1. **Start**: Run `./start-beancount.sh` or `start-beancount.bat`
2. **Edit**: Add transactions to `my-ledger.beancount`
3. **Validate**: Check for errors with `bean-check`
4. **View**: Use Fava web interface at http://localhost:5000
5. **Stop**: Ctrl+C to stop Fava when done

## 📚 Learning Resources

- [Beancount Documentation](https://beancount.github.io/docs/)
- [Beancount Cookbook](https://beancount.github.io/docs/beancount_cookbook.html)
- [Fava Documentation](https://beancount.github.io/fava/)

## 🆘 Getting Help

If you encounter issues:
1. Check this README's troubleshooting section
2. Verify WSL is working: `wsl --list --verbose`
3. Check virtual environment: `which python` (should show beancount-env path)
4. Validate ledger syntax: `bean-check my-ledger.beancount`

---

**Last Updated**: September 22, 2025  
**Beancount Version**: 3.2.0