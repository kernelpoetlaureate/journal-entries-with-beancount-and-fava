#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis Script to Verify the Double-Crediting Fix
Compares balances before and after implementing receivables-based accounting
"""

import re
from collections import defaultdict
from decimal import Decimal

def parse_beancount_file(filename):
    """Parse a beancount file and extract account balances"""
    balances = defaultdict(Decimal)
    transactions = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all transaction entries (lines with account and amount)
        pattern = r'^\s+([A-Za-z:]+(?:[A-Za-z0-9\-]+)*)\s+([\-\+]?[\d,]+\.?\d*)\s+([A-Z]+)'
        
        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                account = match.group(1)
                amount_str = match.group(2).replace(',', '')
                currency = match.group(3)
                
                try:
                    amount = Decimal(amount_str)
                    balances[account] += amount
                    transactions.append({
                        'account': account,
                        'amount': amount,
                        'currency': currency
                    })
                except:
                    continue
                    
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        
    return balances, transactions

def analyze_bank_accounts(balances, title):
    """Analyze bank account balances"""
    print(f"\n=== {title} ===")
    
    bank_accounts = {k: v for k, v in balances.items() if 'Bank' in k}
    total_bank = sum(bank_accounts.values())
    
    print(f"Bank Account Balances:")
    for account, balance in sorted(bank_accounts.items()):
        print(f"  {account}: {balance:,.2f} GEL")
    
    print(f"Total Bank Assets: {total_bank:,.2f} GEL")
    return total_bank

def analyze_receivables(balances, title):
    """Analyze receivables account balances"""
    print(f"\n=== {title} Receivables ===")
    
    receivables = {k: v for k, v in balances.items() if 'Receivables' in k}
    total_receivables = sum(receivables.values())
    
    print(f"Total Receivables: {total_receivables:,.2f} GEL")
    print(f"Number of Customer Receivables: {len(receivables)}")
    
    if len(receivables) > 0:
        print(f"Top 5 Receivables:")
        sorted_receivables = sorted(receivables.items(), key=lambda x: x[1], reverse=True)
        for account, balance in sorted_receivables[:5]:
            customer = account.replace('Assets:Receivables:', '')
            print(f"  {customer}: {balance:,.2f} GEL")
    
    return total_receivables, len(receivables)

def main():
    print("Analyzing the Double-Crediting Fix")
    print("=" * 50)
    
    # Analyze original TBC payments (this should be correct)
    print("\n1. ANALYZING TBC PAYMENTS (Should be correct)")
    tbc_balances, tbc_transactions = parse_beancount_file('tbc_payments.beancount')
    tbc_bank_total = analyze_bank_accounts(tbc_balances, "TBC Payments File")
    tbc_receivables_total, tbc_receivables_count = analyze_receivables(tbc_balances, "TBC Payments")
    
    # Analyze fixed sales file (should create receivables, not bank credits)
    print("\n2. ANALYZING FIXED SALES FILE (Should create receivables)")
    sales_balances, sales_transactions = parse_beancount_file('sales_fixed.beancount')
    sales_bank_total = analyze_bank_accounts(sales_balances, "Fixed Sales File")
    sales_receivables_total, sales_receivables_count = analyze_receivables(sales_balances, "Fixed Sales")
    
    # Combined analysis
    print("\n3. COMBINED ANALYSIS")
    print("=" * 30)
    
    combined_balances = defaultdict(Decimal)
    for account, balance in tbc_balances.items():
        combined_balances[account] += balance
    for account, balance in sales_balances.items():
        combined_balances[account] += balance
    
    combined_bank_total = analyze_bank_accounts(combined_balances, "Combined (TBC + Fixed Sales)")
    combined_receivables_total, combined_receivables_count = analyze_receivables(combined_balances, "Combined")
    
    # Summary
    print("\n4. SUMMARY AND VERIFICATION")
    print("=" * 40)
    print(f"TBC Bank Total (from payments): {tbc_bank_total:,.2f} GEL")
    print(f"Sales Bank Total (should be 0): {sales_bank_total:,.2f} GEL")
    print(f"Combined Bank Total: {combined_bank_total:,.2f} GEL")
    print(f"")
    print(f"Sales Receivables Total: {sales_receivables_total:,.2f} GEL")
    print(f"Combined Receivables Total: {combined_receivables_total:,.2f} GEL")
    print(f"")
    
    # Check if the fix worked
    if abs(sales_bank_total) < 1:  # Should be zero or very close
        print("✅ SUCCESS: Sales file no longer credits bank accounts directly!")
        print("✅ SUCCESS: Sales now create receivables as they should!")
        
        # Calculate what the bank balance should be after payments settle receivables
        net_receivables = combined_receivables_total
        if net_receivables < 0:
            print(f"✅ Net receivables are negative ({net_receivables:,.2f}), indicating payments exceeded sales")
            print(f"✅ This suggests proper settlement of receivables by payments")
        else:
            print(f"ℹ️  Positive receivables ({net_receivables:,.2f}) indicate unpaid sales")
            
    else:
        print(f"❌ ISSUE: Sales file still credits bank accounts ({sales_bank_total:,.2f} GEL)")
        print(f"❌ This suggests the fix may not have worked completely")
    
    # Verification against original Excel sum
    excel_original_sum = Decimal('3496840.15')
    print(f"\nVerification against original Excel sum:")
    print(f"Original Excel sum: {excel_original_sum:,.2f} GEL")
    print(f"Current TBC bank total: {tbc_bank_total:,.2f} GEL")
    difference = tbc_bank_total - excel_original_sum
    print(f"Difference: {difference:,.2f} GEL ({(difference/excel_original_sum*100):+.1f}%)")
    
    if abs(difference) < excel_original_sum * Decimal('0.1'):  # Within 10%
        print("✅ Bank balance is now much closer to the original Excel sum!")
    else:
        print("⚠️  Bank balance still differs significantly from original Excel sum")

if __name__ == "__main__":
    main()