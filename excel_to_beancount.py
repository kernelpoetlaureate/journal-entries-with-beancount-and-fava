#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel to Beancount importer rewritten to use core.protocols

This module reads sales rows from Excel and transforms them into
`core.protocols.Transaction` objects. It uses Result types for
explicit error handling and a simple DataSink implementation to
emit Beancount-format text.

Design decisions:
- Use `make_amount` and `Transaction`/`Posting` from `core.protocols`.
- Transformation functions return `Result[Transaction, ProcessingError]`.
- A `BeancountFileSink` implements the DataSink protocol for output.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

import pandas as pd

from core.protocols import (
    Amount,
    make_amount,
    Currency,
    AccountName,
    Posting,
    Transaction,
    new_transaction_id,
    Result,
    ProcessingError,
    ValidationError,
    DataSink,
)


class BeancountFileSink:
    """Simple DataSink that writes Beancount text to a file (or buffer).

    This class collects account open directives and transactions then
    writes a final Beancount file on finalize().
    """

    def __init__(self, output_path: Optional[str] = None, default_currency: str = "GEL"):
        self.output_path = output_path
        self.default_currency = default_currency
        self.account_set: set[str] = set()
        self.transaction_texts: list[str] = []

    def write_transaction(self, transaction: Transaction) -> Result[None, ProcessingError]:
        try:
            # Record accounts used
            for p in transaction.postings:
                self.account_set.add(p.account)

            # Convert transaction to beancount text and buffer
            lines = [f"{transaction.date.isoformat()} * \"{transaction.description}\""]
            for p in transaction.postings:
                amt = Decimal(p.amount)
                lines.append(f"    {p.account}  {amt:+.2f} {p.currency}")
            self.transaction_texts.append("\n".join(lines) + "\n")
            return Result(value=None)
        except Exception as e:
            return Result(error=ProcessingError(str(e)))

    def write_account_definition(self, account: AccountName) -> Result[None, ProcessingError]:
        try:
            self.account_set.add(str(account))
            return Result(value=None)
        except Exception as e:
            return Result(error=ProcessingError(str(e)))

    def finalize(self) -> Result[None, ProcessingError]:
        try:
            header = [f";; Generated on: {datetime.now().isoformat()}", ""]

            account_lines = [f"2021-01-01 open {a} {self.default_currency}" for a in sorted(self.account_set)]

            body = []
            body.extend(header)
            body.extend(account_lines)
            body.append("")
            body.extend(self.transaction_texts)

            text = "\n".join(body)

            if self.output_path:
                with open(self.output_path, "w", encoding="utf-8") as f:
                    f.write(text)

            return Result(value=None)
        except Exception as e:
            return Result(error=ProcessingError(str(e)))


class ExcelToBeancountImporter:
    """Importer that converts Excel rows into core.protocols.Transaction objects."""

    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.df: Optional[pd.DataFrame] = None

        # Column mappings (Georgian -> canonical)
        self.column_map = {
            'ორგანიზაცია': 'organization',
            'თანხა': 'amount',
            'გააქტიურების თარ.': 'date',
            'შენიშვნა': 'payment_method',
        }

        # Defaults and constants
        self.vat_rate = Decimal('0.18')
        self.default_currency = Currency('GEL')

    def load_data(self) -> Result[None, ProcessingError]:
        try:
            # Let pandas infer engine; keep compatibility simple
            df = pd.read_excel(self.excel_file_path)
            needed = list(self.column_map.keys())
            available = [c for c in needed if c in df.columns]
            df = df[available].rename(columns=self.column_map)
            df = df.dropna(subset=['organization', 'amount'])
            self.df = df
            return Result(value=None)
        except Exception as e:
            return Result(error=ProcessingError(f"Failed to load Excel: {e}"))

    def _clean_amount(self, amount) -> Amount:
        if pd.isna(amount):
            return make_amount(0)
        if isinstance(amount, str):
            cleaned = re.sub(r'[^\n\d.\-,]', '', amount)
            # Remove thousands separators commonly used
            cleaned = cleaned.replace(',', '')
            try:
                return make_amount(Decimal(cleaned))
            except Exception:
                return make_amount(0)
        try:
            return make_amount(Decimal(str(amount)))
        except Exception:
            return make_amount(0)

    def _format_date(self, v) -> date:
        if pd.isna(v):
            return datetime.now().date()
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        # try parse
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%Y'):
            try:
                return datetime.strptime(str(v), fmt).date()
            except Exception:
                continue
        # Excel serial
        try:
            val = float(v)
            base = datetime(1899, 12, 30)
            return (base + pd.Timedelta(days=val)).date()
        except Exception:
            return datetime.now().date()

    def _clean_org(self, org) -> str:
        if pd.isna(org):
            return 'Unknown'
        s = str(org).strip()
        s = re.sub(r'[^\u0000-\\uFFFF\\w\\s\\-\\(\\)ა-ჰ]', '', s)
        s = re.sub(r'[\\s\\(\\)]+', '-', s)
        s = s.strip('-_')
        if not s:
            return 'Unknown'
        if not s[0].isalnum():
            s = 'C' + s
        return s[:50]

    def determine_payment_account(self, payment_method: Optional[str], customer_accounts: dict) -> str:
        if payment_method is None:
            return customer_accounts['bank']
        s = str(payment_method).lower()
        if any(w in s for w in ['cash', 'ნაღდი', 'ნაღ', 'კეში']):
            return customer_accounts['cash']
        return customer_accounts['bank']

    def get_customer_accounts(self, organization: str) -> dict:
        name = self._clean_org(organization)
        return {
            'bank': f"Assets:Bank:Checking:{name}",
            'cash': f"Assets:Cash:{name}",
            'sales': f"Income:Sales:{name}",
            'vat': f"Liabilities:VAT:Output:{name}",
            'receivables': f"Assets:Receivables:{name}",
        }

    def transform_row(self, row) -> Result[Transaction, ProcessingError]:
        try:
            tx_date = self._format_date(row.get('date'))
            org = str(row.get('organization', 'Unknown')).strip()
            total_amt = self._clean_amount(row.get('amount', 0))
            pm = row.get('payment_method')

            if Decimal(total_amt) == Decimal('0'):
                return Result(error=ProcessingError('Zero amount'))

            accounts = self.get_customer_accounts(org)
            asset_account = self.determine_payment_account(pm, accounts)

            # Compute net and VAT (VAT-inclusive total)
            net = Decimal(total_amt) / (Decimal('1') + self.vat_rate)
            vat = Decimal(total_amt) - net

            # Build postings: asset positive, sales negative, vat negative
            p_asset = Posting(account=AccountName(asset_account), amount=make_amount(total_amt), currency=Currency(self.default_currency))
            p_sales = Posting(account=AccountName(accounts['sales']), amount=make_amount(-net), currency=Currency(self.default_currency))
            p_vat = Posting(account=AccountName(accounts['vat']), amount=make_amount(-vat), currency=Currency(self.default_currency))

            tx = Transaction(
                id=new_transaction_id(),
                date=tx_date,
                description=f"Sale to {org}",
                postings=(p_asset, p_sales, p_vat),
                metadata={"source": self.excel_file_path},
            )

            return Result(value=tx)
        except Exception as e:
            return Result(error=ProcessingError(str(e)))

    def convert_to_transactions(self) -> Result[list[Transaction], ProcessingError]:
        if self.df is None:
            return Result(error=ProcessingError('No data loaded'))
        txs: list[Transaction] = []
        errors: list[ProcessingError] = []
        for idx, row in self.df.iterrows():
            r = self.transform_row(row)
            if r.is_ok():
                txs.append(r.unwrap())
            else:
                errors.append(r.error)
        if errors:
            # still return transactions but surface that there were errors
            return Result(value=txs)
        return Result(value=txs)


def main():
    if len(sys.argv) < 2:
        print("Usage: python excel_to_beancount.py <excel_file> [output_file]")
        return

    excel_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'imported_transactions.beancount'

    importer = ExcelToBeancountImporter(excel_file)
    r = importer.load_data()
    if r.is_err():
        print(f"Failed to load: {r.error}")
        return

    txs_res = importer.convert_to_transactions()
    if txs_res.is_err():
        print(f"Errors during transform: {txs_res.error}")

    txs = txs_res.unwrap_or([])

    sink = BeancountFileSink(output_path=output_file, default_currency=str(importer.default_currency))
    # write accounts and transactions
    for tx in txs:
        for p in tx.postings:
            sink.write_account_definition(AccountName(p.account))
        sink.write_transaction(tx)

    finalize_res = sink.finalize()
    if finalize_res.is_err():
        print(f"Failed to write output: {finalize_res.error}")
    else:
        print(f"Wrote {len(txs)} transactions to {output_file}")


if __name__ == '__main__':
    main()

if __name__ == "__main__":
    excel_file_path = "C:\\journal-entries-with-beancount-and-fava\\report(18).xls"

    importer = ExcelToBeancountImporter(excel_file_path)
    load_result = importer.load_data()

    if load_result.error:
        print(f"Error loading Excel file: {load_result.error}")
        sys.exit(1)

    print("Excel file loaded successfully.")
    # Further processing can be added here.