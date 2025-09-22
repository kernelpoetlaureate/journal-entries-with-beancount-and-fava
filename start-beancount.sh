#!/bin/bash

# Beancount Daily Startup Script
# Run this every time you want to use Beancount

echo "💰 Starting Beancount environment..."

# Navigate to home directory
cd ~

# Check if virtual environment exists
if [ ! -d "beancount-env" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run './setup.sh' first to set up Beancount."
    exit 1
fi

# Activate virtual environment
echo "⚡ Activating virtual environment..."
source beancount-env/bin/activate

# Check if ledger file exists
if [ ! -f "my-ledger.beancount" ]; then
    echo "❌ Ledger file 'my-ledger.beancount' not found!"
    echo "Please create your ledger file or run './setup.sh' to create a sample."
    exit 1
fi

# Validate ledger file
echo "🔍 Validating ledger file..."
bean-check my-ledger.beancount

if [ $? -ne 0 ]; then
    echo "❌ Ledger validation failed! Please fix the errors above."
    echo "You can still continue, but Fava may not work properly."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Ledger validation passed!"
fi

echo
echo "🌐 Starting Fava web interface..."
echo "📊 Open your browser and go to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop when you're done"
echo
echo "💡 Tips:"
echo "  - Edit 'my-ledger.beancount' in another terminal/editor"
echo "  - Fava will auto-reload when you save changes"
echo "  - Use 'bean-check my-ledger.beancount' to validate changes"
echo

# Start Fava
fava my-ledger.beancount