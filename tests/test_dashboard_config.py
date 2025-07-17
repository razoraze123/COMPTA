import json
from pathlib import Path

import MOTEUR.compta.dashboard.widget as dw


def test_default_config_created(tmp_path: Path, monkeypatch) -> None:
    cfg_path = tmp_path / "dash.json"
    monkeypatch.setattr(dw, "CONFIG_PATH", cfg_path)
    cfg = dw.load_dashboard_config()
    assert cfg_path.exists()
    assert cfg == dw.DEFAULT_CONFIG
    with cfg_path.open() as fh:
        data = json.load(fh)
    assert data == dw.DEFAULT_CONFIG


def test_build_summary_text_respects_flags() -> None:
    cfg = {
        "show_total_count": False,
        "show_total_amount": True,
        "show_avg_per_month": False,
        "show_chart": True,
    }
    text = dw.build_summary_text(3, 99.5, 10.0, cfg)
    assert "99.50" in text
    assert "Nombre" not in text
    assert "Moyenne" not in text
