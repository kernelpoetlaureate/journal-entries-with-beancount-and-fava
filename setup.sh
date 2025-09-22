#!/bin/bash

# Beancount Setup Script
# Run this once to set up Beancount environment

echo "🚀 Setting up Beancount environment..."
echo "This may take several minutes on first run."
echo

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt install -y \
    build-essential \
    python3 \
    python3-venv \
    python3-pip \
    git \
    meson \
    ninja-build

if [ $? -ne 0 ]; then
    echo "❌ Failed to install system packages"
    exit 1
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
cd ~
python3 -m venv beancount-env

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source beancount-env/bin/activate

# Upgrade pip and install build tools
echo "🔧 Installing build tools..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install meson-python meson ninja

if [ $? -ne 0 ]; then
    echo "❌ Failed to install build tools"
    exit 1
fi

# Install Beancount
echo "💰 Installing Beancount..."
python -m pip install --no-build-isolation -e /mnt/c/Users/giorgi/Downloads/beancount/beancount

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Beancount"
    exit 1
fi

# Install Fava
echo "🌐 Installing Fava web interface..."
pip install fava

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Fava"
    exit 1
fi

# Create sample ledger file if it doesn't exist
if [ ! -f "my-ledger.beancount" ]; then
    echo "📄 Creating sample ledger file..."
    cat > my-ledger.beancount << 'EOF'
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

2025-09-22 * "ATM withdrawal" 
  Assets:Cash      2000.00 INR
  Assets:Bank:Checking
EOF
fi

# Test installation
echo "🧪 Testing installation..."
python -c "import beancount; print('Beancount version:', beancount.__version__)"
bean-check my-ledger.beancount

if [ $? -eq 0 ]; then
    echo
    echo "✅ Setup completed successfully!"
    echo
    echo "📋 Next steps:"
    echo "1. Run './start-beancount.sh' to start using Beancount"
    echo "2. Edit 'my-ledger.beancount' to add your transactions"
    echo "3. Open http://localhost:5000 in your browser when Fava starts"
    echo
    echo "💡 Tip: Make scripts executable with 'chmod +x *.sh'"
else
    echo "❌ Setup completed but validation failed"
    echo "Check the error messages above"
    exit 1
fi