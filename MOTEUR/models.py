from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Supplier:
    """Supplier information."""

    id: Optional[int]
    name: str
    vat_number: Optional[str] = None
    address: Optional[str] = None


@dataclass
class Purchase:
    """Purchase record."""

    id: Optional[int]
    date: str
    invoice_number: str
    supplier_id: int
    label: str
    ht_amount: float
    vat_amount: float
    vat_rate: float
    account_code: str
    due_date: str
    payment_status: str
    payment_date: Optional[str] = None
    payment_method: Optional[str] = None
    is_advance: int = 0
    is_invoice_received: int = 1
    attachment_path: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class EntryLine:
    """Accounting entry line."""

    account: str
    debit: float = 0.0
    credit: float = 0.0
    description: Optional[str] = None


@dataclass
class PurchaseFilter:
    """Filters for querying purchases."""

    start: Optional[str] = None
    end: Optional[str] = None
    supplier_id: Optional[int] = None
    status: Optional[str] = None


@dataclass
class VatLine:
    """VAT summary line."""

    rate: float
    base: float
    vat: float
