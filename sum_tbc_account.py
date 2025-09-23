import re
from decimal import Decimal
from datetime import datetime
import statistics

def sum_account_values(file_path, account_name):
    # Matching both the account pattern and the amount with currency
    account_pattern = re.compile(rf"\s+{re.escape(account_name)}\s+(\d+\.\d+)\s+([A-Z]+)")
    date_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})\s+\*\s+"Payment received from')
    
    total_by_currency = {}
    transaction_count = 0
    sample_transactions = []
    all_amounts = []
    dates = []
    current_date = None
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line_num, line in enumerate(file, 1):
            date_match = date_pattern.search(line)
            if date_match:
                current_date = date_match.group(1)
            
            match = account_pattern.search(line)
            if match:
                transaction_count += 1
                amount = Decimal(match.group(1))
                currency = match.group(2)
                
                if currency not in total_by_currency:
                    total_by_currency[currency] = Decimal('0')
                
                total_by_currency[currency] += amount
                all_amounts.append(amount)
                
                if current_date:
                    dates.append(current_date)
                
                # Store a few sample transactions for display
                if len(sample_transactions) < 5:
                    transaction_info = {
                        'line': line_num,
                        'text': line.strip(),
                        'amount': amount,
                        'currency': currency,
                        'date': current_date
                    }
                    sample_transactions.append(transaction_info)
    
    # Calculate statistics
    stats = {}
    if all_amounts:
        stats['min'] = min(all_amounts)
        stats['max'] = max(all_amounts)
        stats['avg'] = sum(all_amounts) / len(all_amounts)
        stats['median'] = statistics.median(all_amounts)
        
        # Group by date and get monthly summaries
        monthly_totals = {}
        for i, date_str in enumerate(dates):
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                month_key = f"{date.year}-{date.month:02d}"
                
                if month_key not in monthly_totals:
                    monthly_totals[month_key] = Decimal('0')
                
                monthly_totals[month_key] += all_amounts[i]
            except (ValueError, IndexError):
                pass  # Skip if date is invalid or index is out of range
        
        stats['monthly_totals'] = monthly_totals
    
    return total_by_currency, transaction_count, sample_transactions, stats

def main():
    file_path = "tbc_payments.beancount"
    account_name = "Assets:Bank:Checking:TBC"
    
    totals, count, samples, stats = sum_account_values(file_path, account_name)
    
    print(f"=== Analysis of {account_name} ===")
    print(f"Total transactions: {count}")
    
    for currency, amount in totals.items():
        print(f"Total in {currency}: {amount:,.2f}")
    
    print("\nStatistics:")
    print(f"Minimum amount: {stats['min']:,.2f}")
    print(f"Maximum amount: {stats['max']:,.2f}")
    print(f"Average amount: {stats['avg']:,.2f}")
    print(f"Median amount: {stats['median']:,.2f}")
    
    print("\nMonthly Totals:")
    for month, total in sorted(stats['monthly_totals'].items()):
        print(f"{month}: {total:,.2f} GEL")
    
    print("\nSample transactions:")
    for tx in samples:
        print(f"Line {tx['line']} [{tx['date']}]: {tx['text']} ({tx['amount']} {tx['currency']})")
    
if __name__ == "__main__":
    main()