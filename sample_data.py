from pathlib import Path

from MOTEUR.models import Purchase
from MOTEUR.achat_db import add_purchase, pay_purchase, init_db
from MOTEUR.db import connect

DB = Path("demo.db")


def load_demo() -> None:
    init_db(DB)
    with connect(DB) as conn:
        conn.execute("INSERT INTO suppliers (name) VALUES ('Alpha')")
        conn.execute("INSERT INTO suppliers (name) VALUES ('Beta')")
        conn.execute("INSERT INTO suppliers (name) VALUES ('Gamma')")
        conn.commit()
    suppliers = [1, 2, 3]
    # Insert purchases
    purchases = [
        Purchase(None, "2024-01-05", "F001", suppliers[0], "Papeterie", 100.0, 0.0, 20, "601", "2024-02-05", "A_PAYER"),
        Purchase(None, "2024-01-10", "F002", suppliers[1], "Logiciel", 200.0, 0.0, 20, "606", "2024-02-10", "A_PAYER"),
        Purchase(None, "2024-02-01", "F003", suppliers[2], "Mobilier", 300.0, 0.0, 20, "218", "2024-03-01", "A_PAYER"),
        Purchase(None, "2024-02-15", "F004", suppliers[0], "Entretien", 80.0, 0.0, 20, "615", "2024-03-15", "A_PAYER"),
        Purchase(None, "2024-03-01", "F005", suppliers[1], "Fournitures", 50.0, 0.0, 20, "601", "2024-04-01", "A_PAYER"),
    ]
    for p in purchases:
        add_purchase(DB, p)

    # Pay two invoices
    pay_purchase(DB, 1, "2024-02-05", "VIREMENT", 120.0)
    pay_purchase(DB, 2, "2024-02-12", "CB", 240.0)


if __name__ == "__main__":
    load_demo()

