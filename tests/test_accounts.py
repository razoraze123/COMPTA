from MOTEUR.compta.accounting.db import (
    init_db,
    add_account,
    update_account,
    delete_account,
    fetch_accounts,
)


def test_accounts_crud(tmp_path):
    db = tmp_path / "acc.db"
    init_db(db)

    add_account(db, "601", "Achats")
    add_account(db, "701", "Ventes")

    accts = fetch_accounts(db)
    assert ("601", "Achats") in accts
    assert ("701", "Ventes") in accts

    update_account(db, "601", "Fournitures")
    accts = fetch_accounts(db)
    assert ("601", "Fournitures") in accts

    delete_account(db, "701")
    accts = fetch_accounts(db)
    assert all(code != "701" for code, _ in accts)
