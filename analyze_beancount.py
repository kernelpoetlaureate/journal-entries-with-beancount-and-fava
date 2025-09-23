import re
from decimal import Decimal

def analyze_beancount_file(file_path):
    """Analyze the beancount file for account totals and transaction counts"""
    tbc_account = "Assets:Bank:Checking:TBC"
    receivable_pattern = re.compile(r"Assets:Receivables:")
    
    # Counters
    transaction_count = 0
    tbc_total = Decimal('0')
    receivables_total = Decimal('0')
    
    # Parse the file
    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip to the first transaction (after account openings)
        for line in f:
            if line.strip() and line[0].isdigit() and ' * ' in line:
                # Found first transaction
                break
        
        # Now process all transactions
        current_date = None
        for line in f:
            line = line.strip()
            
            # Extract date of transaction
            if line and line[0].isdigit() and ' * ' in line:
                transaction_count += 1
                current_date = line.split()[0]  # Extract date
                
            # Extract postings
            elif line.startswith(tbc_account):
                # TBC account posting
                amount_match = re.search(r"(\d+\.\d+)\s+GEL", line)
                if amount_match:
                    amount = Decimal(amount_match.group(1))
                    tbc_total += amount
                    
            # Receivables account posting
            elif receivable_pattern.search(line):
                # Receivables account posting
                amount_match = re.search(r"-(\d+\.\d+)\s+GEL", line)
                if amount_match:
                    amount = Decimal(amount_match.group(1))
                    receivables_total += amount
    
    # Print results
    print(f"Analysis of {file_path}:")
    print(f"Total transactions: {transaction_count}")
    print(f"TBC account total: {tbc_total:,.2f} GEL")
    print(f"Receivables total: {receivables_total:,.2f} GEL")
    print(f"Difference: {abs(tbc_total - receivables_total):,.2f} GEL")
    
    # Check for double entries
    double_count = transaction_count * 2
    print(f"\nBalance check:")
    print(f"Total postings expected (2 per transaction): {double_count}")
    
    return {
        'transaction_count': transaction_count,
        'tbc_total': tbc_total,
        'receivables_total': receivables_total
    }

if __name__ == "__main__":
    # Analyze the beancount file
    analyze_beancount_file("tbc_payments.beancount")