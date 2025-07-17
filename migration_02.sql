CREATE UNIQUE INDEX IF NOT EXISTS unq_supplier_invoice
  ON purchases(supplier_id, invoice_number);

PRAGMA foreign_keys = ON;
ALTER TABLE purchases
  ADD CONSTRAINT fk_purchase_account
  FOREIGN KEY (account_code) REFERENCES accounts(code);

CREATE TRIGGER IF NOT EXISTS trg_purchase_vat
BEFORE INSERT ON purchases
FOR EACH ROW
BEGIN
  SELECT CASE
    WHEN ROUND(NEW.ht_amount * NEW.vat_rate / 100, 2) <> NEW.vat_amount
    THEN RAISE(FAIL, 'VAT amount inconsistent with HT × rate')
  END;
END;

CREATE TRIGGER IF NOT EXISTS trg_purchase_vat_up
BEFORE UPDATE ON purchases
FOR EACH ROW
BEGIN
  SELECT CASE
    WHEN ROUND(NEW.ht_amount * NEW.vat_rate / 100, 2) <> NEW.vat_amount
    THEN RAISE(FAIL, 'VAT amount inconsistent with HT × rate')
  END;
END;

CREATE TABLE IF NOT EXISTS sequences (
    journal TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    next_number INTEGER NOT NULL,
    PRIMARY KEY (journal, fiscal_year)
);

CREATE INDEX IF NOT EXISTS idx_purchases_date     ON purchases(date);
CREATE INDEX IF NOT EXISTS idx_purchases_supplier ON purchases(supplier_id);
CREATE INDEX IF NOT EXISTS idx_entries_date       ON entries(date);
