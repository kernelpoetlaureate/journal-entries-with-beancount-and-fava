Sample CSV format and column mappings for the Beancount importer

Columns in `sample_transactions.csv`:
- date: Date of transaction (ISO YYYY-MM-DD preferred).
- description: Merchant / narration string.
- amount: Numeric amount. Positive for credits (inflows), negative for debits (outflows) in the account's currency.
- currency: ISO currency code (e.g., INR).
- type: debit|credit indicator from the raw file (optional).
- account: The source account (e.g., Assets:Bank:Savings).

Mapping rules used by the importer script:
- date -> transaction date, normalized to YYYY-MM-DD.
- description -> narration (quoted in Beancount output).
- amount/currency -> posting amount on the source account.
  - Positive amounts are treated as credits (inflow) to the account; negative as debits (outflow).
- The counterposting (to balance) is chosen by simple rules:
  - If description contains keywords like "salary", map to Income:Salary (amount elided so beancount interpolates).
  - If amount < 0 (outflow) and no keyword matched, map to Expenses:Unknown.
  - If amount > 0 (refund/credit) and no keyword matched, map to Income:Unknown.

Next steps: run `python scripts/importer.py scripts/sample_transactions.csv out.beancount` to generate an output beancount file.
