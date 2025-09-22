#!/usr/bin/env python3
"""
Enhanced analysis of the imported Beancount file
"""

def analyze_beancount_file(filename):
    """Analyze the imported Beancount file and provide statistics"""
    print(f"Analyzing {filename}...")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"File contains {len(lines)} lines")
        
        # Statistics
        open_accounts = 0
        transactions = 0
        postings = 0
        total_amount = 0
        dates = set()
        accounts_used = set()
        
        current_transaction = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('2025-01-01 open '):
                open_accounts += 1
                account = line.split()[2]
                accounts_used.add(account)
            
            elif ' * "' in line and not line.startswith('    '):
                transactions += 1
                current_transaction = line
                # Extract date
                date = line.split()[0]
                dates.add(date)
            
            elif line.startswith('    ') and any(acc in line for acc in ['Assets:', 'Expenses:', 'Income:']):
                postings += 1
                parts = line.strip().split()
                
                # Extract account name
                account = parts[0]
                accounts_used.add(account)
                
                # Extract amount if present (some postings are interpolated)
                if len(parts) >= 3 and 'INR' in line:
                    try:
                        amount_str = parts[-2]
                        amount = float(amount_str)
                        total_amount += abs(amount)  # Use absolute value for total volume
                    except (ValueError, IndexError):
                        pass
        
        print(f"\nStatistics:")
        print(f"  - {open_accounts} account declarations")
        print(f"  - {transactions} transactions")
        print(f"  - {postings} postings")
        print(f"  - Transaction date range: {min(dates) if dates else 'N/A'} to {max(dates) if dates else 'N/A'}")
        print(f"  - Total transaction volume: {total_amount:,.2f} INR")
        
        print(f"\nAccounts used:")
        for account in sorted(accounts_used):
            print(f"  - {account}")
        
        # Sample transactions
        print(f"\nSample transactions:")
        transaction_count = 0
        for line in lines:
            if ' * "' in line and not line.startswith('    '):
                print(f"  {line.strip()}")
                transaction_count += 1
                if transaction_count >= 5:
                    break
        
        return True
        
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

if __name__ == "__main__":
    analyze_beancount_file("imported_transactions.beancount")