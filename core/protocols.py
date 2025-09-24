"""
Foundation Protocol Layer - The Kernel of Our Financial System

This module defines the fundamental contracts and data types that all other
layers depend upon. These protocols are designed for stability and minimal
interface surface area, following the Unix philosophy of "mechanism, not policy."

Design Principles:
1. Immutability: All core types are immutable to prevent hidden state changes
2. Explicit Failure: All operations that can fail return Result types
3. Zero-Copy: Data structures designed for efficient memory usage
4. Composition: Small interfaces that compose into larger behaviors
"""

from __future__ import annotations
from typing import Protocol, Iterator, Sequence, NewType, Union, Generic, TypeVar
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import uuid

# === FUNDAMENTAL VALUE TYPES ===
# These are our "machine word" equivalents - atomic, immutable, well-defined

# Amount: Always stored as precise decimal, never float
# Following accounting principle: monetary amounts must be exact
Amount = NewType('Amount', Decimal)


def make_amount(value: Union[str, int, float, Decimal]) -> Amount:
    """Create precise monetary amount, rounded to 2 decimal places"""
    decimal_val = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return Amount(decimal_val)

# Currency: ISO 4217 currency codes (3-letter strings)
Currency = NewType('Currency', str)

# AccountName: Beancount-style hierarchical account names
# Format: Type:Category:Subcategory (e.g., "Assets:Bank:Checking")
AccountName = NewType('AccountName', str)

# TransactionId: Unique identifier for each transaction
TransactionId = NewType('TransactionId', str)


def new_transaction_id() -> TransactionId:
    """Generate unique transaction identifier"""
    return TransactionId(f"txn_{uuid.uuid4().hex[:12]}")

# === ACCOUNT CLASSIFICATION ===
# Following standard accounting equation: Assets = Liabilities + Equity
# Income and Expenses are temporary accounts that roll into Equity


class AccountType(Enum):
    """Standard accounting account types with clear semantics"""
    ASSETS = "Assets"           # Things we own (positive balance = debit)
    LIABILITIES = "Liabilities" # Things we owe (positive balance = credit)
    EQUITY = "Equity"          # Net worth (positive balance = credit)
    INCOME = "Income"          # Revenue streams (positive balance = credit)
    EXPENSES = "Expenses"      # Cost categories (positive balance = debit)


@dataclass(frozen=True)
class AccountInfo:
    """Immutable account metadata"""
    name: AccountName
    account_type: AccountType
    currency: Currency
    description: str = ""

    def is_debit_account(self) -> bool:
        """True for accounts where increases are debits (Assets, Expenses)"""
        return self.account_type in (AccountType.ASSETS, AccountType.EXPENSES)


# === TRANSACTION FUNDAMENTALS ===
# Every financial event becomes a balanced set of postings


@dataclass(frozen=True)
class Posting:
    """
    Single posting in double-entry system

    A posting represents one side of a transaction - either money flowing
    into an account (positive) or out of an account (negative).
    """
    account: AccountName
    amount: Amount
    currency: Currency

    def __post_init__(self):
        """Validate posting invariants"""
        if self.amount == Amount(Decimal('0')):
            raise ValueError("Posting amount cannot be zero")

    def is_debit(self) -> bool:
        """True if this posting increases a debit-normal account"""
        return self.amount > 0

    def is_credit(self) -> bool:
        """True if this posting increases a credit-normal account"""  
        return self.amount < 0


@dataclass(frozen=True)
class Transaction:
    """
    Complete financial transaction with balanced postings

    Invariant: sum(posting.amount for posting in postings) == 0
    This enforces the fundamental accounting equation.
    """
    id: TransactionId
    date: date
    description: str
    postings: tuple[Posting, ...]  # Immutable sequence
    metadata: dict[str, str]       # Additional context (tags, notes, etc.)

    def __post_init__(self):
        """Enforce transaction invariants"""
        if len(self.postings) < 2:
            raise ValueError("Transaction must have at least 2 postings")

        # Check that transaction balances
        total = sum(posting.amount for posting in self.postings)
        if abs(total) > Decimal('0.01'):  # Allow for rounding errors
            raise ValueError(f"Transaction does not balance: {total}")

        # Check all postings use same currency  
        currencies = {posting.currency for posting in self.postings}
        if len(currencies) > 1:
            raise ValueError(f"Mixed currencies in transaction: {currencies}")

    @property
    def currency(self) -> Currency:
        """Transaction currency (all postings must match)"""
        return self.postings[0].currency

    def get_posting(self, account: AccountName) -> Posting | None:
        """Get posting for specific account, if any"""
        for posting in self.postings:
            if posting.account == account:
                return posting
        return None


# === RESULT TYPE FOR ERROR HANDLING ===
# Following Rust/functional programming patterns for explicit error handling

T = TypeVar('T')
E = TypeVar('E')


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Result type for operations that can fail"""
    value: T | None = None
    error: E | None = None

    def __post_init__(self):
        if (self.value is None) == (self.error is None):
            raise ValueError("Result must have exactly one of value or error")

    def is_ok(self) -> bool:
        return self.value is not None

    def is_err(self) -> bool:
        return self.error is not None

    def unwrap(self) -> T:
        """Get value or raise exception"""
        if self.error is not None:
            raise Exception(f"Result contained error: {self.error}")
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get value or return default"""
        return self.value if self.is_ok() else default


# Common error types
class ValidationError(Exception):
    """Data validation failed"""
    pass


class ProcessingError(Exception):
    """Data processing failed"""
    pass


class ConfigurationError(Exception):
    """Configuration invalid"""
    pass


# === DATA SOURCE/SINK PROTOCOLS ===
# These define how data flows into and out of our system


class DataRecord(Protocol):
    """Raw data record from any source"""
    def get_field(self, field_name: str) -> str | None: ...
    def get_all_fields(self) -> dict[str, str]: ...


class DataSource(Protocol):
    """Universal data input interface"""

    def validate_format(self) -> Result[None, ValidationError]:
        """Check if data source is in expected format"""
        ...

    def extract_records(self) -> Iterator[Result[DataRecord, ProcessingError]]:
        """Extract raw data records, yielding errors for invalid records"""
        ...

    def get_metadata(self) -> dict[str, str]:
        """Get source metadata (file path, format, etc.)"""
        ...


class DataSink(Protocol):
    """Universal data output interface"""

    def write_transaction(self, transaction: Transaction) -> Result[None, ProcessingError]:
        """Write single transaction"""
        ...

    def write_account_definition(self, account: AccountInfo) -> Result[None, ProcessingError]:
        """Define account for use in transactions"""
        ...

    def finalize(self) -> Result[None, ProcessingError]:
        """Complete output and validate result"""
        ...


# === TRANSFORMATION PROTOCOLS ===
# These define how raw data becomes financial transactions


class TransformationRule(Protocol):
    """Rule for converting raw data to transactions"""

    def applies_to(self, record: DataRecord) -> bool:
        """Check if this rule can process the given record"""
        ...

    def transform(self, record: DataRecord) -> Result[Transaction, ProcessingError]:
        """Convert record to transaction"""
        ...

    def get_required_accounts(self) -> set[AccountName]:
        """Get accounts that must exist for this rule to work"""
        ...


class AccountMapper(Protocol):
    """Maps business entities to account names"""

    def map_customer_account(
        self, 
        customer_name: str, 
        account_type: AccountType
    ) -> Result[AccountName, ValidationError]:
        """Generate account name for customer"""
        ...

    def validate_account_name(self, name: AccountName) -> Result[None, ValidationError]:
        """Check if account name follows conventions"""
        ...


# === PROCESSING ENGINE PROTOCOL ===
# Orchestrates the entire data flow


class ProcessingEngine(Protocol):
    """Main processing orchestrator"""

    def add_source(self, source: DataSource) -> None:
        """Register data source"""
        ...

    def add_rule(self, rule: TransformationRule) -> None:
        """Register transformation rule"""
        ...

    def add_sink(self, sink: DataSink) -> None:
        """Register data sink"""
        ...

    def process(self) -> Result[ProcessingSummary, ProcessingError]:
        """Execute full processing pipeline"""
        ...


@dataclass(frozen=True)
class ProcessingSummary:
    """Summary of processing results"""
    transactions_processed: int
    transactions_successful: int
    transactions_failed: int
    accounts_created: int
    errors: tuple[ProcessingError, ...]


# === VALIDATION PROTOCOL ===
# Cross-cutting validation that ensures data integrity


class DataValidator(Protocol):
    """Validates data consistency and business rules"""

    def validate_transaction(self, transaction: Transaction) -> Result[None, ValidationError]:
        """Validate individual transaction"""
        ...

    def validate_account_usage(
        self, 
        transactions: Sequence[Transaction],
        accounts: Sequence[AccountInfo]
    ) -> Result[None, ValidationError]:
        """Validate that all used accounts are properly defined"""
        ...

    def validate_business_rules(
        self, 
        transactions: Sequence[Transaction]
    ) -> Result[None, ValidationError]:
        """Validate business-specific rules (VAT calculations, etc.)"""
        ...
