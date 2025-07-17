from pathlib import Path

from MOTEUR.compta.achats.db import init_db, add_purchase
from MOTEUR.compta.accounting.db import export_fec
from MOTEUR.compta.models import Purchase


def test_export_fec_generates_file(tmp_path: Path) -> None:
    db = tmp_path / "p.db"
    init_db(db)
    from MOTEUR.compta.db import connect
    with connect(db) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('Test')")
        conn.commit()
    add_purchase(
        db,
        Purchase(
            None,
            "2024-01-05",
            "INV1",
            1,
            "Test",
            100.0,
            0.0,
            20,
            "601",
            "2024-02-05",
            "A_PAYER",
        ),
    )
    dest = tmp_path / "fec.csv"
    export_fec(db, 2024, dest)
    assert dest.exists()
    with dest.open() as fh:
        lines = fh.readlines()
    # header + 3 lines
    assert len(lines) == 4
