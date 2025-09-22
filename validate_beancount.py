#!/usr/bin/env python3
"""
Simple verification script for Beancount files
"""

def validate_beancount_file(filename):
    """Basic validation of Beancount file format"""
    print(f"Validating {filename}...")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"File contains {len(lines)} lines")
        
        # Count different types of entries
        open_accounts = 0
        transactions = 0
        postings = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('open '):
                open_accounts += 1
            elif ' * "' in line and not line.startswith('    '):
                transactions += 1
            elif line.startswith('    ') and ('INR' in line or any(acc in line for acc in ['Assets:', 'Expenses:', 'Income:'])):
                postings += 1
        
        print(f"Found:")
        print(f"  - {open_accounts} account declarations")
        print(f"  - {transactions} transactions")
        print(f"  - {postings} postings")
        
        # Check for basic formatting issues
        issues = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith(';;'):
                # Check for unbalanced quotes
                if line.count('"') % 2 != 0:
                    issues.append(f"Line {i}: Unbalanced quotes")
                
                # Check for proper indentation on postings
                if line.startswith('    ') and 'Assets:' in line:
                    if not any(curr in line for curr in ['INR', 'USD', 'EUR']):
                        # This might be the second posting without amount (interpolated)
                        pass
        
        if issues:
            print(f"\nPotential issues found:")
            for issue in issues[:10]:  # Show first 10 issues
                print(f"  - {issue}")
        else:
            print("\nNo obvious formatting issues found!")
        
        return True
        
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

if __name__ == "__main__":
    validate_beancount_file("imported_transactions.beancount")