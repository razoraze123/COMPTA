CREATE VIEW IF NOT EXISTS supplier_balance_v AS
SELECT s.id      AS supplier_id,
       s.name    AS supplier_name,
       ROUND(SUM(CASE WHEN el.debit>0 THEN el.debit ELSE -el.credit END),2) AS balance
FROM suppliers s
LEFT JOIN entries   e   ON e.ref IN (
      SELECT invoice_number FROM purchases WHERE supplier_id = s.id)
LEFT JOIN entry_lines el ON el.entry_id = e.id
WHERE el.account IN ('401','408','4091')
GROUP BY s.id;
