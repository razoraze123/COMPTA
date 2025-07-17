from pathlib import Path

from MOTEUR.compta.vente_db import (
    init_db,
    add_sale,
    update_sale,
    delete_sale,
    fetch_all_sales,
)


def test_sales_crud(tmp_path: Path) -> None:
    db = tmp_path / "sales.db"
    init_db(db)

    sid = add_sale(db, "2024-01-02", "Test", 10.5)
    rows = fetch_all_sales(db)
    assert len(rows) == 1
    assert rows[0][0] == sid

    update_sale(db, sid, "2024-01-03", "Updated", 15.0)
    rows = fetch_all_sales(db)
    assert rows[0][1:] == ("2024-01-03", "Updated", 15.0)

    delete_sale(db, sid)
    assert fetch_all_sales(db) == []
