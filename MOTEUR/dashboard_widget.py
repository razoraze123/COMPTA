from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .achat_db import fetch_all_purchases, init_db

BASE_DIR = Path(__file__).resolve().parent.parent
# Default path to the SQLite database used in AchatWidget
DB_PATH = BASE_DIR / "compta.db"

try:
    import matplotlib

    matplotlib.use("QtAgg")  # Use Qt backend for PySide6
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

    MPL_AVAILABLE = True
except Exception:  # pragma: no cover - matplotlib is optional
    MPL_AVAILABLE = False


class DashboardWidget(QWidget):
    """Widget displaying purchase statistics with an optional graph."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        init_db(DB_PATH)

        layout = QVBoxLayout(self)
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
        self.summary_label.setText(
            f"Nombre d'achats : {total}\n"
            f"Total : {amount:.2f} \u20ac\n"
            f"Moyenne par mois : {avg:.2f} \u20ac"
        )

    def _update_chart(self, by_month: dict[str, float]) -> None:
        if not MPL_AVAILABLE or not self.figure:
            return
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

