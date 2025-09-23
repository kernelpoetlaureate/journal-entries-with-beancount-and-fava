import re
from decimal import Decimal
from collections import defaultdict

def analyze_beancount_accounts(file_path):
    """Analyze all accounts in the beancount file to understand the full accounting picture"""
    # Counters
    accounts = defaultdict(lambda: Decimal('0'))
    transaction_count = 0
    account_postings = 0
    
    # Parse the file line by line
    transaction_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\s+\*\s+")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Check for transaction lines
            if transaction_pattern.match(line):
                transaction_count += 1
            
            # Check for posting lines (indented with account and amount)
            elif line.startswith("    "):  # Account postings are indented
                # Extract account name
                parts = line.split()
                if len(parts) >= 3:
                    account_name = parts[0]
                    
                    # Extract amount and currency
                    try:
                        amount = Decimal(parts[1])
                        currency = parts[2]
                        
                        if currency == "GEL":
                            accounts[account_name] += amount
                            account_postings += 1
                    except (ValueError, IndexError):
                        pass  # Skip lines that don't match our expected format
    
    # Print results
    print(f"Analysis of all accounts in {file_path}:")
    print(f"Total transactions: {transaction_count}")
    print(f"Total account postings: {account_postings}")
    
    # Group accounts by type
    account_types = defaultdict(lambda: Decimal('0'))
    for account, balance in accounts.items():
        account_type = account.split(':')[0]
        account_types[account_type] += balance
    
    # Print account hierarchy with balances
    print("\nAccount Hierarchy:")
    
    # First print totals by type
    print("\nAccount Type Totals:")
    for account_type, balance in sorted(account_types.items()):
        print(f"{account_type}: {balance:,.2f} GEL")
    
    # Print individual accounts grouped by type
    print("\nDetailed Account Balances:")
    for account_type in sorted(account_types.keys()):
        print(f"\n{account_type}:")
        # Get all accounts of this type
        type_accounts = {a: b for a, b in accounts.items() if a.startswith(account_type + ':')}
        
        # Calculate the hierarchy
        account_hierarchy = defaultdict(lambda: Decimal('0'))
        
        # Group by first two levels
        for account, balance in type_accounts.items():
            parts = account.split(':')
            if len(parts) >= 2:
                level2 = f"{parts[0]}:{parts[1]}"
                account_hierarchy[level2] += balance
        
        # Print second level accounts
        for account, balance in sorted(account_hierarchy.items()):
            print(f"  {account}: {balance:,.2f} GEL")
            
            # Find all accounts under this second level
            for sub_account, sub_balance in sorted(type_accounts.items()):
                if sub_account.startswith(account + ':'):
                    print(f"    {sub_account}: {sub_balance:,.2f} GEL")
    
    # Verify that accounts balance (should sum to zero)
    total_balance = sum(accounts.values())
    print(f"\nBalance check: {total_balance:,.2f} GEL")
    print(f"System is balanced: {total_balance == 0}")
    
    return {
        'transaction_count': transaction_count,
        'accounts': dict(accounts),
        'account_types': dict(account_types),
        'total_balance': total_balance
    }

if __name__ == "__main__":
    # Analyze the beancount file
    analyze_beancount_accounts("tbc_payments.beancount")