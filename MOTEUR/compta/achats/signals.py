from PySide6.QtCore import QObject, Signal

class AchatSignals(QObject):
    """Signals emitted by the purchases module."""

    supplier_changed = Signal()
    entry_changed    = Signal()


signals = AchatSignals()
