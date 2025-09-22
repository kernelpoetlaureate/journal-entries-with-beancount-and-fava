"""Simple CSV -> Beancount converter

Usage:
    python scripts\importer.py input.csv output.beancount

This script is intentionally small and easy to adapt. It reads a CSV with the
columns: date, description, amount, currency, type, account

It writes a .beancount file with one transaction per row. The counteraccount
is chosen by simple keyword rules and amount sign. One posting amount is left
blank for Beancount to interpolate when appropriate.
"""
import sys
import csv
from decimal import Decimal, InvalidOperation
from datetime import datetime
try:
    import pandas as pd
except Exception:
    pd = None

KEYWORD_ACCOUNT_MAP = {
    'salary': 'Income:Salary',
    'payroll': 'Income:Salary',
    'coffee': 'Expenses:Food:Coffee',
    'latte': 'Expenses:Food:Coffee',
    'subscription': 'Expenses:Services:Subscriptions',
    'atm': 'Expenses:Cash',
    'withdrawal': 'Expenses:Cash',
    'refund': 'Income:Refunds',
}

DEFAULT_EXPENSE = 'Expenses:Unknown'
DEFAULT_INCOME = 'Income:Unknown'


def choose_counter_account(description: str, amount: Decimal) -> str:
    desc = (description or '').lower()
    for kw, acct in KEYWORD_ACCOUNT_MAP.items():
        if kw in desc:
            return acct
    return DEFAULT_EXPENSE if amount < 0 else DEFAULT_INCOME


def format_amount(amount: Decimal, currency: str) -> str:
    # Format with two decimal places; beancount expects a space before currency
    return f"{amount:.2f} {currency}"


def parse_decimal(s: str) -> Decimal:
    try:
        return Decimal(s)
    except (InvalidOperation, TypeError):
        # try to clean common thousands separators
        if s is None:
            return Decimal('0')
        s2 = s.replace(',', '')
        return Decimal(s2)


def normalize_date(s: str) -> str:
    # accept YYYY-MM-DD or common variants
    if not s:
        return datetime.today().strftime('%Y-%m-%d')
    try:
        d = datetime.fromisoformat(s)
        return d.strftime('%Y-%m-%d')
    except ValueError:
        # try common formats
        for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
            try:
                d = datetime.strptime(s, fmt)
                return d.strftime('%Y-%m-%d')
            except ValueError:
                continue
        raise


def row_to_transaction(row: dict) -> str:
    date = normalize_date(row.get('date'))
    description = row.get('description', '').strip()
    raw_amount = row.get('amount', '0')
    currency = row.get('currency', 'INR').strip()
    account = row.get('account', 'Assets:Bank:Unknown').strip()

    amount = parse_decimal(raw_amount)

    # In our CSV positive=credit/inflow to account; negative=debit/outflow
    # For Beancount, we post the signed amount on the source account and leave
    # the counter account amount blank (so beancount interpolates) and choose
    # counter account by keywords.
    counter_account = choose_counter_account(description, amount)

    lines = []
    # Transaction header
    header_flag = '*'  # use '*' to mark cleared/uncertain
    header = f"{date} {header_flag} \"{description}\""
    lines.append(header)

    # Posting: source account with explicit amount
    amt_text = format_amount(amount, currency)
    lines.append(f"    {account}    {amt_text}")

    # Counterposting: leave amount blank so beancount interpolates
    lines.append(f"    {counter_account}")

    return '\n'.join(lines) + '\n\n'


def convert_csv_to_beancount(csv_path: str, out_path: str):
    # Use pandas if available for more robust parsing, else fall back to csv
    if pd is not None:
        df = pd.read_csv(csv_path, dtype=str).fillna('')
        txs = [row_to_transaction(row.to_dict()) for _, row in df.iterrows()]
    else:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            txs = [row_to_transaction(row) for row in reader]

    # Prepend account openings for accounts seen (basic heuristic)
    accounts = set()
    for row in csv.DictReader(open(csv_path, newline='', encoding='utf-8')):
        accounts.add(row.get('account') or 'Assets:Bank:Unknown')
    openings = []
    for acct in sorted(accounts):
        openings.append(f"open {acct}    ; Imported account")
    openings.append('')

    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('\n'.join(openings))
        out.write('\n'.join(txs))


def main(argv):
    if len(argv) < 3:
        print('Usage: python scripts\\importer.py input.csv output.beancount')
        return 2
    csv_path = argv[1]
    out_path = argv[2]
    convert_csv_to_beancount(csv_path, out_path)
    print(f'Wrote beancount file: {out_path}')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
