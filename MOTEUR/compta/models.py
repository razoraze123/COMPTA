from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Supplier:
    """Supplier information."""

    id: Optional[int]
    name: str
    vat_number: Optional[str] = None
    address: Optional[str] = None


@dataclass
class Purchase:
    """Purchase record.

    The model originally stored the HT and VAT amounts as well as an
    ``invoice_number``.  The revamped UI now works with the total amount
    including VAT (TTC) and an internal reference called ``piece``.
    ``ht_amount`` and ``vat_amount`` are therefore computed when needed and are
    no longer part of the public API.
    """

    id: Optional[int]
    date: str
    piece: str
    supplier_id: int
    label: str
    ttc_amount: float
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
