from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from PySide6.QtCore import Slot, Signal
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QHBoxLayout,
    QPushButton,
)

from .achat_db import fetch_all_purchases, init_db

BASE_DIR = Path(__file__).resolve().parent.parent
# Default path to the SQLite database used in AchatWidget
DB_PATH = BASE_DIR / "compta.db"
CONFIG_PATH = Path(__file__).with_name("dashboard_config.json")

DEFAULT_CONFIG = {
    "show_total_count": True,
    "show_total_amount": True,
    "show_avg_per_month": True,
    "show_chart": True,
}

try:
    import matplotlib

    matplotlib.use("QtAgg")  # Use Qt backend for PySide6
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

    MPL_AVAILABLE = True
except Exception:  # pragma: no cover - matplotlib is optional
    MPL_AVAILABLE = False


def load_dashboard_config() -> dict:
    """Return dashboard configuration from :data:`CONFIG_PATH`."""
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return {**DEFAULT_CONFIG, **{k: bool(v) for k, v in data.items()}}
        except Exception:
            return DEFAULT_CONFIG.copy()
    CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False))
    return DEFAULT_CONFIG.copy()


def save_dashboard_config(config: dict) -> None:
    """Write *config* to :data:`CONFIG_PATH`."""
    with CONFIG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)


def build_summary_text(total: int, amount: float, avg: float, config: dict) -> str:
    """Return summary text based on *config*."""
    lines: list[str] = []
    if config.get("show_total_count", True):
        lines.append(f"Nombre d'achats : {total}")
    if config.get("show_total_amount", True):
        lines.append(f"Total : {amount:.2f} \u20ac")
    if config.get("show_avg_per_month", True):
        lines.append(f"Moyenne par mois : {avg:.2f} \u20ac")
    return "\n".join(lines)


class DashboardWidget(QWidget):
    """Widget displaying purchase statistics with an optional graph."""

    journal_requested = Signal()
    grand_livre_requested = Signal()
    scraping_summary_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        init_db(DB_PATH)

        self.config = load_dashboard_config()

        layout = QVBoxLayout(self)

        nav_layout = QHBoxLayout()
        journal_btn = QPushButton("Journal")
        journal_btn.clicked.connect(self.journal_requested.emit)
        nav_layout.addWidget(journal_btn)

        grand_btn = QPushButton("Grand Livre")
        grand_btn.clicked.connect(self.grand_livre_requested.emit)
        nav_layout.addWidget(grand_btn)

        scrap_btn = QPushButton("Dernier scraping")
        scrap_btn.clicked.connect(self.scraping_summary_requested.emit)
        nav_layout.addWidget(scrap_btn)
        layout.addLayout(nav_layout)

        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

        if MPL_AVAILABLE:
            self.figure = Figure(figsize=(5, 3))
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)
        else:  # pragma: no cover - depends on matplotlib being installed
            self.figure = None
            self.canvas = None
            layout.addWidget(
                QLabel("matplotlib requis pour l'affichage du graphique")
            )

        config_layout = QHBoxLayout()
        self.count_cb = QCheckBox("Nombre")
        self.amount_cb = QCheckBox("Total")
        self.avg_cb = QCheckBox("Moyenne/mois")
        self.chart_cb = QCheckBox("Graphique")
        for key, cb in [
            ("show_total_count", self.count_cb),
            ("show_total_amount", self.amount_cb),
            ("show_avg_per_month", self.avg_cb),
            ("show_chart", self.chart_cb),
        ]:
            cb.setChecked(self.config.get(key, True))
            cb.stateChanged.connect(self._config_changed)
            config_layout.addWidget(cb)
        layout.addLayout(config_layout)

        self.refresh()

    # ------------------------------------------------------------------
    @Slot()
    def _config_changed(self) -> None:
        """Persist config and refresh widgets when checkboxes change."""
        self.config = {
            "show_total_count": self.count_cb.isChecked(),
            "show_total_amount": self.amount_cb.isChecked(),
            "show_avg_per_month": self.avg_cb.isChecked(),
            "show_chart": self.chart_cb.isChecked(),
        }
        save_dashboard_config(self.config)
        self.refresh()

    # ------------------------------------------------------------------
    def _load_purchases(self) -> list[tuple[int, str, str, float]]:
        return fetch_all_purchases(DB_PATH)

    def _compute_metrics(self, rows: list[tuple[int, str, str, float]]):
        total_count = len(rows)
        total_amount = sum(r[3] for r in rows)

        by_month: dict[str, float] = defaultdict(float)
        for _pid, date_str, _label, amount in rows:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            key = dt.strftime("%Y-%m")
            by_month[key] += amount
        avg_per_month = total_amount / len(by_month) if by_month else 0.0
        return total_count, total_amount, avg_per_month, by_month

    def _update_summary(self, total: int, amount: float, avg: float) -> None:
        text = build_summary_text(total, amount, avg, self.config)
        self.summary_label.setText(text)
        self.summary_label.setVisible(bool(text))

    def _update_chart(self, by_month: dict[str, float]) -> None:
        if not MPL_AVAILABLE or not self.figure:
            return
        if not self.config.get("show_chart", True):
            if self.canvas:
                self.canvas.hide()
            return
        if self.canvas:
            self.canvas.show()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        months = sorted(by_month)
        amounts = [by_month[m] for m in months]
        ax.bar(months, amounts, color="#539ecd")
        ax.set_xlabel("Mois")
        ax.set_ylabel("Montant")
        ax.set_title("Achats par mois")
        self.figure.autofmt_xdate(rotation=45)
        self.canvas.draw()

    # Public API --------------------------------------------------------
    @Slot()
    def refresh(self) -> None:
        """Reload purchases from the database and update widgets."""
        rows = self._load_purchases()
        total, amount, avg, by_month = self._compute_metrics(rows)
        self._update_summary(total, amount, avg)
        self._update_chart(by_month)

