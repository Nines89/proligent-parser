"""GUI per Proligent Parser – griglia dati con filtri Excel-style."""

from __future__ import annotations

import sys


def _build_splash_base():
    """Paint the static splash artwork (no progress bar)."""
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QFont,
        QLinearGradient,
        QPainter,
        QPainterPath,
        QPen,
        QPixmap,
        QRadialGradient,
    )

    w, h = 520, 320
    pm = QPixmap(w, h)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)

    radius = 18.0
    card = QPainterPath()
    card.addRoundedRect(QRectF(0, 0, w, h), radius, radius)

    grad = QLinearGradient(0, 0, w, h)
    grad.setColorAt(0.0, QColor("#0d47a1"))
    grad.setColorAt(0.45, QColor("#1565c0"))
    grad.setColorAt(1.0, QColor("#00838f"))
    p.fillPath(card, QBrush(grad))

    spot = QRadialGradient(QPointF(90, 70), 220)
    spot.setColorAt(0.0, QColor(255, 255, 255, 55))
    spot.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setClipPath(card)
    p.fillRect(0, 0, w, h, QBrush(spot))

    p.setBrush(Qt.NoBrush)
    for cx, cy, r, alpha in (
        (460, 40, 120, 28),
        (480, 280, 90, 22),
        (40, 260, 70, 20),
    ):
        pen = QPen(QColor(255, 255, 255, alpha), 1.5)
        p.setPen(pen)
        p.drawEllipse(QPointF(cx, cy), r, r)
        pen.setWidthF(1.0)
        pen.setColor(QColor(255, 255, 255, alpha // 2))
        p.setPen(pen)
        p.drawEllipse(QPointF(cx, cy), r * 0.62, r * 0.62)

    accent = QLinearGradient(72, 0, 280, 0)
    accent.setColorAt(0.0, QColor("#4fc3f7"))
    accent.setColorAt(1.0, QColor(79, 195, 247, 0))
    p.fillRect(72, 168, 208, 3, QBrush(accent))

    badge_r = 28
    bx, by = 72, 78
    badge = QPainterPath()
    badge.addRoundedRect(QRectF(bx, by, badge_r * 2, badge_r * 2), 12, 12)
    p.fillPath(badge, QColor(255, 255, 255, 28))
    pen = QPen(QColor(255, 255, 255, 90), 1.2)
    p.setPen(pen)
    p.drawPath(badge)

    mark_font = QFont("Segoe UI", 22, QFont.Bold)
    p.setFont(mark_font)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(bx, by, badge_r * 2, badge_r * 2), Qt.AlignCenter, "P")

    title_font = QFont("Segoe UI", 26, QFont.Bold)
    p.setFont(title_font)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(140, 78, 340, 40), Qt.AlignVCenter | Qt.AlignLeft, "Proligent")

    sub_font = QFont("Segoe UI", 14)
    sub_font.setWeight(QFont.Light)
    p.setFont(sub_font)
    p.setPen(QColor(255, 255, 255, 200))
    p.drawText(QRectF(140, 116, 340, 28), Qt.AlignVCenter | Qt.AlignLeft, "Parser")

    status_font = QFont("Segoe UI", 10)
    p.setFont(status_font)
    p.setPen(QColor(255, 255, 255, 170))
    p.drawText(
        QRectF(72, 210, 376, 24),
        Qt.AlignVCenter | Qt.AlignLeft,
        "Avvio in corso\u2026",
    )

    foot_font = QFont("Segoe UI", 8)
    p.setFont(foot_font)
    p.setPen(QColor(255, 255, 255, 110))
    p.drawText(
        QRectF(72, 275, 376, 20),
        Qt.AlignVCenter | Qt.AlignLeft,
        "Analytics  ·  Production reports",
    )

    p.end()
    return pm


def _compose_splash_frame(base, progress: float):
    """Copy the base artwork and draw the animated progress shimmer."""
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath

    pm = base.copy()
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    track_x, track_y, track_w, track_h = 72, 248, 376, 6
    track = QPainterPath()
    track.addRoundedRect(QRectF(track_x, track_y, track_w, track_h), 3, 3)
    p.fillPath(track, QColor(255, 255, 255, 35))

    chunk_w = 120
    max_x = track_w - chunk_w
    chunk_x = track_x + (progress % 1.0) * max_x
    chunk = QPainterPath()
    chunk.addRoundedRect(QRectF(chunk_x, track_y, chunk_w, track_h), 3, 3)
    chunk_grad = QLinearGradient(chunk_x, 0, chunk_x + chunk_w, 0)
    chunk_grad.setColorAt(0.0, QColor(79, 195, 247, 40))
    chunk_grad.setColorAt(0.5, QColor("#80deea"))
    chunk_grad.setColorAt(1.0, QColor(79, 195, 247, 40))
    p.fillPath(chunk, QBrush(chunk_grad))
    p.end()
    return pm


# Show splash immediately when launched as a script, before heavy imports.
_STARTUP_SPLASH = None
if __name__ == "__main__":
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QApplication, QSplashScreen

    class _StartupSplash(QSplashScreen):
        def __init__(self) -> None:
            self._base = _build_splash_base()
            super().__init__(_compose_splash_frame(self._base, 0.0))
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self._t = 0.0
            self._timer = QTimer(self)
            self._timer.setInterval(40)
            self._timer.timeout.connect(self._animate)
            self._timer.start()

        def _animate(self) -> None:
            self._t = (self._t + 0.035) % 1.0
            self.setPixmap(_compose_splash_frame(self._base, self._t))

        def finish(self, widget) -> None:
            self._timer.stop()
            super().finish(widget)

    _app = QApplication.instance() or QApplication(sys.argv)
    _STARTUP_SPLASH = _StartupSplash()
    _STARTUP_SPLASH.show()
    _app.processEvents()

import json
import threading
from pathlib import Path
from typing import Any

import pandas as pd
from PySide6.QtCore import (
    QAbstractTableModel,
    QDate,
    QModelIndex,
    QPropertyAnimation,
    QSortFilterProxyModel,
    Qt,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

_SAVED_SHORTCUTS_FILE = Path(__file__).parent / "saved_shortcuts.json"

FONT_FAMILY = "Segoe UI"
FONT_SIZE_TABLE = 13
ROW_HEIGHT = 30

APP_STYLESHEET = """
QWidget {
    background-color: #fafafa;
    color: #212121;
}
QMainWindow {
    background-color: #fafafa;
}
"""


# ---------------------------------------------------------------------------
# Loading overlay
# ---------------------------------------------------------------------------

class LoadingOverlay(QWidget):
    """Semi-transparent overlay with spinner and message, shown during operations."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: transparent;")
        self.hide()

        self._angle = 0
        self._message = "Caricamento…"

        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._tick)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)

        self._lbl_msg = QLabel(self._message)
        self._lbl_msg.setAlignment(Qt.AlignCenter)
        self._lbl_msg.setStyleSheet(
            "font-size:16px; font-weight:bold; color:white;"
            "background:transparent; padding:8px 20px;"
        )
        lay.addWidget(self._lbl_msg)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedWidth(280)
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet(
            "QProgressBar { border:none; background:#546e7a; border-radius:3px; }"
            "QProgressBar::chunk { background:#4fc3f7; border-radius:3px; }"
        )
        lay.addWidget(self._progress, alignment=Qt.AlignCenter)

    def show_loading(self, message: str = "Caricamento…") -> None:
        self._message = message
        self._lbl_msg.setText(message)
        self.raise_()
        self.resize(self.parentWidget().size())
        self.show()
        self._timer.start()

    def hide_loading(self) -> None:
        self._timer.stop()
        self.hide()

    def set_message(self, msg: str) -> None:
        self._message = msg
        self._lbl_msg.setText(msg)

    def _tick(self) -> None:
        self._angle = (self._angle + 4) % 360
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 140))

        cx = self.width() // 2
        cy = self.height() // 2 - 40
        radius = 28

        pen = QPen(QColor(255, 255, 255, 60), 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        pen.setColor(QColor(79, 195, 247))
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawArc(
            cx - radius, cy - radius, radius * 2, radius * 2,
            self._angle * 16, 90 * 16,
        )

        painter.end()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.resize(self.parentWidget().size())


# ---------------------------------------------------------------------------
# Table model
# ---------------------------------------------------------------------------

class PandasModel(QAbstractTableModel):

    def __init__(self) -> None:
        super().__init__()
        self._df = pd.DataFrame()
        self._bold_font = QFont(FONT_FAMILY, FONT_SIZE_TABLE, QFont.Bold)

    def set_dataframe(self, df: pd.DataFrame) -> None:
        self.beginResetModel()
        self._df = df.reset_index(drop=True)
        self.endResetModel()

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._df.columns)

    _LINK_FONT = None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        val = self._df.iat[index.row(), index.column()]
        if role == Qt.DisplayRole:
            return "" if pd.isna(val) else str(val)
        col_name = self._df.columns[index.column()]
        if col_name == "Status":
            s = str(val).strip().upper() if not pd.isna(val) else ""
            if role == Qt.BackgroundRole:
                colors = {"PASS": "#c8e6c9", "FAIL": "#ffcdd2", "ABORTED": "#fff9c4"}
                if s in colors:
                    return QColor(colors[s])
            if role == Qt.ForegroundRole:
                colors = {"PASS": "#1b5e20", "FAIL": "#b71c1c", "ABORTED": "#e65100"}
                if s in colors:
                    return QColor(colors[s])
            if role == Qt.FontRole:
                return self._bold_font
        if col_name == "Documents" and self._has_download_urls():
            display_val = "" if pd.isna(val) else str(val)
            if display_val and display_val != "0":
                if role == Qt.ForegroundRole:
                    return QColor("#1565c0")
                if role == Qt.FontRole:
                    if self._LINK_FONT is None:
                        self._LINK_FONT = QFont(FONT_FAMILY, FONT_SIZE_TABLE)
                        self._LINK_FONT.setUnderline(True)
                    return self._LINK_FONT
                if role == Qt.ToolTipRole:
                    return "Clicca per scaricare i documenti"
        return None

    def _has_download_urls(self) -> bool:
        return "_download_url" in self._df.columns

    def get_download_url(self, row: int) -> str:
        if not self._has_download_urls():
            return ""
        val = self._df.iat[row, self._df.columns.get_loc("_download_url")]
        return "" if pd.isna(val) else str(val)

    def get_unit_view(self, row: int) -> str:
        if "_unit_view" not in self._df.columns:
            return ""
        val = self._df.iat[row, self._df.columns.get_loc("_unit_view")]
        return "" if pd.isna(val) else str(val)

    def headerData(self, section: int, orient: Qt.Orientation,
                   role: int = Qt.DisplayRole) -> Any:
        if orient == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self._df.columns[section])
        if orient == Qt.Vertical and role == Qt.DisplayRole:
            return str(section + 1)
        return None


# ---------------------------------------------------------------------------
# Filter proxy
# ---------------------------------------------------------------------------

class ExcelFilterProxy(QSortFilterProxyModel):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._allowed: dict[int, set[str]] = {}

    def set_column_allowed(self, col: int, values: set[str] | None) -> None:
        if values is None:
            self._allowed.pop(col, None)
        else:
            self._allowed[col] = values
        self.invalidateRowsFilter()

    def clear_filters(self) -> None:
        self._allowed.clear()
        self.invalidateRowsFilter()

    def get_active_filters(self) -> dict[int, set[str]]:
        return dict(self._allowed)

    def filterAcceptsRow(self, row: int, parent: QModelIndex) -> bool:
        model = self.sourceModel()
        for col, allowed in self._allowed.items():
            idx = model.index(row, col, parent)
            cell = str(model.data(idx, Qt.DisplayRole) or "")
            if cell not in allowed:
                return False
        return True


# ---------------------------------------------------------------------------
# Filter dialog
# ---------------------------------------------------------------------------

class FilterDialog(QDialog):

    def __init__(self, col_name: str, all_values: list[str],
                 checked: set[str] | None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Filtra: {col_name}")
        self.setMinimumSize(360, 500)

        self.setStyleSheet("background:#fafafa; color:#212121;")

        lay = QVBoxLayout(self)
        lay.setSpacing(8)

        srch = QLineEdit()
        srch.setPlaceholderText("Cerca...")
        srch.setStyleSheet("font-size:14px; padding:6px; color:#212121; background:white;")
        srch.textChanged.connect(self._search)
        lay.addWidget(srch)

        row = QHBoxLayout()
        b1 = QPushButton("Seleziona tutto")
        b1.setStyleSheet("color:#424242; background:#e0e0e0;")
        b1.clicked.connect(self._all)
        b2 = QPushButton("Deseleziona tutto")
        b2.setStyleSheet("color:#424242; background:#e0e0e0;")
        b2.clicked.connect(self._none)
        row.addWidget(b1)
        row.addWidget(b2)
        lay.addLayout(row)

        self._list = QListWidget()
        self._list.setStyleSheet(
            "QListWidget { font-size:14px; color:#212121; background:white; }"
            "QListWidget::item { padding:4px; color:#212121; }"
        )
        self._vals = sorted(set(all_values))
        if checked is None:
            checked = set(self._vals)
        for v in self._vals:
            it = QListWidgetItem(v if v else "(vuoto)")
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if v in checked else Qt.Unchecked)
            it.setData(Qt.UserRole, v)
            self._list.addItem(it)
        lay.addWidget(self._list, stretch=1)

        info = QLabel(f"{len(self._vals)} valori unici")
        info.setStyleSheet("color:#757575; font-size:12px;")
        lay.addWidget(info)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        self.result_values: set[str] | None = None

    def _search(self, text: str) -> None:
        t = text.lower()
        for i in range(self._list.count()):
            it = self._list.item(i)
            it.setHidden(t not in (it.data(Qt.UserRole) or "").lower())

    def _all(self) -> None:
        for i in range(self._list.count()):
            it = self._list.item(i)
            if not it.isHidden():
                it.setCheckState(Qt.Checked)

    def _none(self) -> None:
        for i in range(self._list.count()):
            it = self._list.item(i)
            if not it.isHidden():
                it.setCheckState(Qt.Unchecked)

    def accept(self) -> None:
        picked = set()
        all_on = True
        for i in range(self._list.count()):
            it = self._list.item(i)
            if it.checkState() == Qt.Checked:
                picked.add(it.data(Qt.UserRole))
            else:
                all_on = False
        self.result_values = None if all_on else picked
        super().accept()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):

    _login_done = Signal(bool, str)
    _query_done = Signal(object, str)
    _progress_msg = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Proligent Parser")
        self.resize(1500, 900)

        self._client = None
        self._logged_in = False
        self._downloading = False
        self._current_df = pd.DataFrame()
        self._col_uniq: dict[int, list[str]] = {}

        self._build_ui()
        self._overlay = LoadingOverlay(self.centralWidget())
        self._connect()

    def _build_ui(self) -> None:
        c = QWidget()
        self.setCentralWidget(c)
        root = QVBoxLayout(c)
        root.setContentsMargins(10, 10, 10, 4)
        root.setSpacing(6)

        # ── Login ──
        lr = QHBoxLayout()
        self._btn_login = QPushButton("  Login Proligent  ")
        self._btn_login.setStyleSheet(
            "font-size:14px; font-weight:bold; padding:8px 24px;"
            "background:#1565c0; color:white; border:none; border-radius:4px;"
        )
        self._lbl_login = QLabel("  Non connesso")
        self._lbl_login.setStyleSheet("font-size:14px; color:#757575;")
        lr.addWidget(self._btn_login)
        lr.addWidget(self._lbl_login)
        lr.addStretch()
        root.addLayout(lr)

        # ── Tabs ──
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            "QTabWidget::pane { border:1px solid #ccc; background:white; }"
            "QTabBar::tab { font-size:13px; padding:8px 18px; color:#424242;"
            " border:1px solid #ccc; border-bottom:none;"
            " background:#eeeeee; border-top-left-radius:4px;"
            " border-top-right-radius:4px; }"
            "QTabBar::tab:selected { background:white; color:#212121; font-weight:bold; }"
        )
        root.addWidget(self._tabs)

        # Tab 1: query libera
        t1 = QWidget()
        g = QGridLayout(t1)
        g.setSpacing(8)
        g.setContentsMargins(12, 12, 12, 8)

        fields = [
            (0, 0, "Report:", "_cmb_report"),
            (0, 2, "Stazione:", "_txt_station"),
            (0, 4, "Prodotto:", "_txt_product"),
            (0, 6, "Operazione:", "_txt_operation"),
            (1, 0, "Data da:", "_txt_date_from"),
            (1, 2, "Data a:", "_txt_date_to"),
            (1, 4, "Status:", "_cmb_status"),
            (1, 6, "Serial:", "_txt_serial"),
            (2, 0, "Processo:", "_txt_process"),
            (2, 2, "Modalita':", "_txt_mode"),
            (2, 4, "Utente:", "_txt_user"),
            (2, 6, "Max righe:", "_spn_top"),
        ]

        for row, col, label, attr in fields:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:13px; color:#424242;")
            g.addWidget(lbl, row, col)

            if attr == "_cmb_report":
                w = QComboBox()
                w.setEditable(True)
                w.addItems([
                    "OperationRuns", "SequenceRuns", "Measurements",
                    "Activity", "CycleTime", "BacklogTime", "FailedRuns",
                    "Yield", "FirstPassYield", "LastPassYield",
                    "WorkInProgress", "StationUtilization",
                ])
            elif attr == "_cmb_status":
                w = QComboBox()
                w.addItems(["(tutti)", "Pass", "Fail", "Aborted"])
            elif attr == "_spn_top":
                w = QSpinBox()
                w.setRange(0, 100_000)
                w.setValue(10_000)
                w.setSpecialValueText("Illimitato")
            else:
                w = QLineEdit()

            w.setStyleSheet("font-size:13px; padding:4px 6px; color:#212121; background:white;")
            g.addWidget(w, row, col + 1)
            setattr(self, attr, w)

        self._btn_query = QPushButton("  Esegui Query  ")
        self._btn_query.setEnabled(False)
        self._btn_query.setStyleSheet(
            "font-size:14px; font-weight:bold; padding:12px 28px;"
            "background:#2e7d32; color:white; border:none; border-radius:4px;"
        )
        g.addWidget(self._btn_query, 0, 8, 3, 1)

        hint = QLabel(
            "Suggerimento: lancia la query senza filtri, poi clicca sulle "
            "intestazioni della griglia per filtrare con i valori reali."
        )
        hint.setStyleSheet("font-size:12px; color:#9e9e9e; font-style:italic;")
        hint.setWordWrap(True)
        g.addWidget(hint, 3, 0, 1, 9)

        # Tab "Query libera" nascosta — pronta per uso futuro
        self._tab_query = t1  # prevent garbage collection
        # self._tabs.addTab(t1, "  Query libera  ")

        # Tab: shortcut
        t2 = QWidget()
        v2 = QVBoxLayout(t2)
        v2.setContentsMargins(12, 12, 12, 8)
        v2.setSpacing(8)

        # Row 1: combo + carica
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        l2 = QLabel("Shortcut:")
        l2.setStyleSheet("font-size:13px; color:#424242;")
        row1.addWidget(l2)

        self._cmb_shortcut = QComboBox()
        self._cmb_shortcut.setEditable(True)
        self._cmb_shortcut.setInsertPolicy(QComboBox.NoInsert)
        self._cmb_shortcut.lineEdit().setPlaceholderText(
            "Seleziona un shortcut salvato o incolla un UUID"
        )
        self._cmb_shortcut.setStyleSheet(
            "QComboBox { font-size:13px; padding:6px; color:#212121;"
            "  background:white; border:1px solid #bdbdbd; border-radius:3px; }"
            "QComboBox::drop-down { subcontrol-position:center right;"
            "  width:28px; border-left:1px solid #bdbdbd; background:#eeeeee; }"
            "QComboBox::down-arrow { image:none; border:none;"
            "  border-left:4px solid transparent; border-right:4px solid transparent;"
            "  border-top:6px solid #424242; width:0; height:0; }"
            "QComboBox QAbstractItemView { color:#212121; background:white;"
            "  border:1px solid #bdbdbd; selection-background-color:#e3f2fd;"
            "  selection-color:#212121; outline:none; }"
            "QComboBox QAbstractItemView::item { padding:6px 10px; color:#212121; }"
            "QComboBox QAbstractItemView::item:hover { background:#e3f2fd; }"
        )
        self._cmb_shortcut.setMinimumWidth(400)
        row1.addWidget(self._cmb_shortcut, stretch=1)

        self._btn_shortcut = QPushButton("  Carica  ")
        self._btn_shortcut.setEnabled(False)
        self._btn_shortcut.setStyleSheet(
            "font-size:14px; font-weight:bold; padding:10px 28px;"
            "background:#e65100; color:white; border:none; border-radius:4px;"
        )
        row1.addWidget(self._btn_shortcut)
        v2.addLayout(row1)

        # Row 2: salva / elimina
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self._txt_shortcut_label = QLineEdit()
        self._txt_shortcut_label.setPlaceholderText("Nome per questo shortcut (opzionale)")
        self._txt_shortcut_label.setStyleSheet(
            "font-size:12px; padding:5px 8px; color:#212121; background:white;"
        )
        row2.addWidget(self._txt_shortcut_label, stretch=1)

        self._btn_save_sc = QPushButton("  Salva  ")
        self._btn_save_sc.setStyleSheet(
            "font-size:12px; font-weight:bold; padding:5px 18px;"
            "background:#2e7d32; color:white; border:none; border-radius:3px;"
        )
        row2.addWidget(self._btn_save_sc)

        self._btn_del_sc = QPushButton("  Elimina  ")
        self._btn_del_sc.setStyleSheet(
            "font-size:12px; font-weight:bold; padding:5px 18px;"
            "background:#c62828; color:white; border:none; border-radius:3px;"
        )
        row2.addWidget(self._btn_del_sc)

        v2.addLayout(row2)

        self._tabs.addTab(t2, "  Shortcut UUID  ")
        self._tabs.tabBar().setVisible(self._tabs.count() > 1)

        self._load_saved_shortcuts()

        # ── Toolbar: date filters ──
        date_row = QHBoxLayout()
        date_row.setSpacing(6)

        _DATE_EDIT_CSS = (
            "QDateEdit { font-size:12px; padding:4px 6px; color:#212121;"
            "  background:white; border:1px solid #bdbdbd; border-radius:3px; }"
            "QDateEdit::drop-down { subcontrol-position:center right;"
            "  width:20px; border-left:1px solid #bdbdbd; background:#eeeeee; }"
            "QDateEdit::down-arrow { image:none; border:none;"
            "  border-left:3px solid transparent; border-right:3px solid transparent;"
            "  border-top:5px solid #424242; width:0; height:0; }"
        )
        _QUICK_BTN_CSS = (
            "font-size:11px; padding:4px 10px; color:#212121; background:#e3f2fd;"
            " border:1px solid #90caf9; border-radius:3px;"
        )

        lbl_da = QLabel("Da:")
        lbl_da.setStyleSheet("font-size:12px; color:#424242;")
        date_row.addWidget(lbl_da)
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_from.setStyleSheet(_DATE_EDIT_CSS)
        date_row.addWidget(self._date_from)

        lbl_a = QLabel("A:")
        lbl_a.setStyleSheet("font-size:12px; color:#424242;")
        date_row.addWidget(lbl_a)
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setStyleSheet(_DATE_EDIT_CSS)
        date_row.addWidget(self._date_to)

        self._btn_apply_date = QPushButton("Filtra date")
        self._btn_apply_date.setStyleSheet(
            "font-size:12px; font-weight:bold; padding:4px 14px;"
            " color:white; background:#1565c0; border:none; border-radius:3px;"
        )
        date_row.addWidget(self._btn_apply_date)

        self._btn_clear_date = QPushButton("Tutte")
        self._btn_clear_date.setStyleSheet(
            "font-size:11px; padding:4px 10px; color:#424242; background:#e0e0e0;"
            " border:1px solid #bdbdbd; border-radius:3px;"
        )
        date_row.addWidget(self._btn_clear_date)

        date_row.addSpacing(10)

        self._btn_24h = QPushButton("Ultime 24h")
        self._btn_24h.setStyleSheet(_QUICK_BTN_CSS)
        date_row.addWidget(self._btn_24h)

        self._btn_7d = QPushButton("Ultima settimana")
        self._btn_7d.setStyleSheet(_QUICK_BTN_CSS)
        date_row.addWidget(self._btn_7d)

        self._btn_30d = QPushButton("Ultimo mese")
        self._btn_30d.setStyleSheet(_QUICK_BTN_CSS)
        date_row.addWidget(self._btn_30d)

        date_row.addStretch()
        root.addLayout(date_row)

        # ── Toolbar: grid filters + export ──
        tb = QHBoxLayout()
        self._btn_clear = QPushButton("Rimuovi filtri griglia")
        self._btn_clear.setStyleSheet(
            "font-size:12px; padding:4px 10px; color:#424242; background:#e0e0e0;"
            " border:1px solid #bdbdbd; border-radius:3px;"
        )
        tb.addWidget(self._btn_clear)
        self._lbl_filt = QLabel("")
        self._lbl_filt.setStyleSheet("font-size:12px; color:#757575;")
        tb.addWidget(self._lbl_filt, stretch=1)
        self._btn_export = QPushButton("Esporta CSV")
        self._btn_export.setEnabled(False)
        self._btn_export.setStyleSheet(
            "font-size:12px; padding:4px 10px; color:#424242; background:#e0e0e0;"
            " border:1px solid #bdbdbd; border-radius:3px;"
        )
        tb.addWidget(self._btn_export)
        root.addLayout(tb)

        hint2 = QLabel(
            "Clicca su un'intestazione di colonna per filtrare (stile Excel)  |  "
            "Click destro su una cella per filtrare/escludere quel valore"
        )
        hint2.setStyleSheet("font-size:11px; color:#9e9e9e; font-style:italic;")
        root.addWidget(hint2)

        # ── Grid ──
        self._model = PandasModel()
        self._proxy = ExcelFilterProxy()
        self._proxy.setSourceModel(self._model)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.ExtendedSelection)
        self._table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self._table.horizontalHeader().setDefaultSectionSize(150)
        self._table.horizontalHeader().setMinimumSectionSize(70)
        self._table.horizontalHeader().setSectionsMovable(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)

        table_font = QFont(FONT_FAMILY, FONT_SIZE_TABLE)
        self._table.setFont(table_font)

        self._table.setStyleSheet(
            "QTableView {"
            f"  font-size: {FONT_SIZE_TABLE}pt;"
            "  color: #212121;"
            "  gridline-color: #d4d4d4;"
            "  background: white;"
            "  alternate-background-color: #f5f8fc;"
            "  selection-background-color: #bbdefb;"
            "  selection-color: #000;"
            "  border: 1px solid #bbb;"
            "}"
            "QTableView::item { padding: 4px 10px; color: #212121; }"
            "QHeaderView::section {"
            "  font-size: 11pt; font-weight: bold;"
            "  background: #37474f; color: white;"
            "  padding: 7px 10px;"
            "  border: none; border-right: 1px solid #546e7a;"
            "  border-bottom: 2px solid #263238;"
            "}"
            "QHeaderView::section:hover { background: #455a64; color: white; }"
        )

        # ── Result tabs: Dati (grid) + Dashboard ──
        self._result_tabs = QTabWidget()
        self._result_tabs.setStyleSheet(
            "QTabWidget::pane { border:1px solid #ccc; background:white; }"
            "QTabBar::tab { font-size:13px; padding:8px 22px; color:#424242;"
            " border:1px solid #ccc; border-bottom:none;"
            " background:#eeeeee; border-top-left-radius:4px;"
            " border-top-right-radius:4px; margin-right:2px; }"
            "QTabBar::tab:selected { background:white; color:#1565c0;"
            " font-weight:bold; }"
        )

        dati_tab = QWidget()
        dati_lay = QVBoxLayout(dati_tab)
        dati_lay.setContentsMargins(0, 0, 0, 0)
        dati_lay.addWidget(self._table)
        self._result_tabs.addTab(dati_tab, "  Dati  ")

        self._dashboard = None
        self._dashboard_placeholder = QWidget()
        placeholder_lay = QVBoxLayout(self._dashboard_placeholder)
        placeholder_lay.addStretch()
        ph_lbl = QLabel("Apri questa scheda per caricare la dashboard.")
        ph_lbl.setAlignment(Qt.AlignCenter)
        ph_lbl.setStyleSheet("font-size:14px; color:#9e9e9e;")
        placeholder_lay.addWidget(ph_lbl)
        placeholder_lay.addStretch()
        self._dashboard_tab_index = self._result_tabs.addTab(
            self._dashboard_placeholder, "  Dashboard  "
        )

        root.addWidget(self._result_tabs, stretch=1)

        # ── Status bar ──
        sb = QStatusBar()
        sb.setStyleSheet("font-size:13px; color:#424242; background:#eeeeee;")
        self.setStatusBar(sb)
        self._statusbar = sb
        self._lbl_count = QLabel("Nessun dato")
        self._lbl_count.setStyleSheet("color:#424242;")
        sb.addPermanentWidget(self._lbl_count)

    def _connect(self) -> None:
        self._btn_login.clicked.connect(self._on_login)
        self._btn_query.clicked.connect(self._on_query)
        self._btn_shortcut.clicked.connect(self._on_shortcut)
        self._btn_save_sc.clicked.connect(self._on_save_shortcut)
        self._btn_del_sc.clicked.connect(self._on_del_shortcut)
        self._btn_export.clicked.connect(self._on_export)
        self._btn_clear.clicked.connect(self._on_clear)
        self._btn_apply_date.clicked.connect(self._apply_date_filter)
        self._btn_clear_date.clicked.connect(self._clear_date_filter)
        self._btn_24h.clicked.connect(lambda: self._quick_date_filter(1))
        self._btn_7d.clicked.connect(lambda: self._quick_date_filter(7))
        self._btn_30d.clicked.connect(lambda: self._quick_date_filter(30))
        self._login_done.connect(self._login_result)
        self._query_done.connect(self._query_result)
        self._progress_msg.connect(self._overlay.set_message)
        self._download_finished.connect(self._on_download_finished)
        self._unit_view_done.connect(self._on_unit_view_done)
        self._table.horizontalHeader().sectionClicked.connect(self._hdr_click)
        self._table.clicked.connect(self._on_cell_click)
        self._table.customContextMenuRequested.connect(self._ctx_menu)
        self._result_tabs.currentChanged.connect(self._on_result_tab_changed)

    def _get_client(self):
        if self._client is None:
            from proligent_client import ProligentClient
            self._client = ProligentClient()
        return self._client

    def _ensure_dashboard(self) -> None:
        if self._dashboard is not None:
            return
        from gui_dashboard import DashboardWidget

        self._dashboard = DashboardWidget()
        self._result_tabs.removeTab(self._dashboard_tab_index)
        self._result_tabs.insertTab(
            self._dashboard_tab_index, self._dashboard, "  Dashboard  "
        )

    # ── Login ──

    @Slot()
    def _on_login(self) -> None:
        self._btn_login.setEnabled(False)
        self._lbl_login.setText("  Connessione...")
        self._lbl_login.setStyleSheet("font-size:14px; color:#757575;")
        self._overlay.show_loading("Connessione a Proligent…")
        threading.Thread(target=self._do_login, daemon=True).start()

    def _do_login(self) -> None:
        try:
            self._get_client().login(headless=True)
            self._login_done.emit(True, "")
        except Exception as e:
            self._login_done.emit(False, str(e))

    @Slot(bool, str)
    def _login_result(self, ok: bool, err: str) -> None:
        self._overlay.hide_loading()
        self._btn_login.setEnabled(True)
        if ok:
            self._logged_in = True
            self._lbl_login.setText("  Connesso")
            self._lbl_login.setStyleSheet("font-size:14px; color:#2e7d32; font-weight:bold;")
            self._btn_query.setEnabled(True)
            self._btn_shortcut.setEnabled(True)
        else:
            self._lbl_login.setText("  Errore")
            self._lbl_login.setStyleSheet("font-size:14px; color:red;")
            QMessageBox.critical(self, "Errore Login", err)

    # ── Query ──

    @Slot()
    def _on_query(self) -> None:
        self._run(self._q_params)

    @Slot()
    def _on_shortcut(self) -> None:
        self._run(self._s_params)

    def _run(self, fn) -> None:
        if not self._logged_in:
            return
        self._btn_query.setEnabled(False)
        self._btn_shortcut.setEnabled(False)
        self._statusbar.showMessage("Query in corso...")
        self._overlay.show_loading("Esecuzione query…")
        self._pfn = fn
        threading.Thread(target=self._do_q, daemon=True).start()

    def _q_params(self) -> dict:
        kw: dict[str, Any] = {"_r": self._cmb_report.currentText().strip() or "OperationRuns"}
        txt_map = [
            (self._txt_station, "station"), (self._txt_product, "product"),
            (self._txt_operation, "operation"), (self._txt_date_from, "date_from"),
            (self._txt_date_to, "date_to"), (self._txt_serial, "serial"),
            (self._txt_process, "processKey"), (self._txt_mode, "processModeKey"),
            (self._txt_user, "userKey"),
        ]
        for w, k in txt_map:
            v = w.text().strip()
            if v:
                kw[k] = v
        st = self._cmb_status.currentText().strip()
        if st and st != "(tutti)":
            kw["status"] = st
        top = self._spn_top.value()
        if top > 0:
            kw["top"] = top
        return kw

    def _s_params(self) -> dict:
        text = self._cmb_shortcut.currentText().strip()
        # The combo display format is "label  —  uuid" or just "uuid"
        if "  —  " in text:
            u = text.split("  —  ")[-1].strip()
        else:
            u = text
        if not u:
            raise ValueError("Inserisci un UUID shortcut.")
        return {"_r": u}

    def _do_q(self) -> None:
        try:
            p = self._pfn()
            r = p.pop("_r")

            import proligent_client as _pc
            original_log = _pc._log

            def _gui_log(msg: str) -> None:
                original_log(msg)
                import re
                if "paginazione via Discovery" in msg:
                    self._progress_msg.emit("Apertura Discovery nel browser…")
                elif "Pagina" in msg and "click" in msg:
                    m = re.search(r"Pagina (\d+)/(\d+)", msg)
                    if m:
                        self._progress_msg.emit(
                            f"Raccolta pagina {m.group(1)} di {m.group(2)}…"
                        )
                elif "Discovery:" in msg and "pagine trovate" in msg:
                    m = re.search(r"(\d+) pagine", msg)
                    if m:
                        self._progress_msg.emit(
                            f"Trovate {m.group(1)} pagine, raccolta dati…"
                        )
                elif "Discovery totale:" in msg:
                    m = re.search(r"(\d+) record", msg)
                    if m:
                        self._progress_msg.emit(
                            f"Completato: {m.group(1)} record raccolti."
                        )
                elif "Pagina" in msg and "date_to=" in msg:
                    self._progress_msg.emit(f"Raccolta dati… {msg.strip()}")
                elif "Paginazione automatica" in msg:
                    self._progress_msg.emit("Raccolta pagine aggiuntive…")

            _pc._log = _gui_log
            try:
                df = self._get_client().query(r, **p)
            finally:
                _pc._log = original_log

            self._query_done.emit(df, "")
        except Exception as e:
            self._query_done.emit(None, str(e))

    @Slot(object, str)
    def _query_result(self, df: pd.DataFrame | None, err: str) -> None:
        self._overlay.hide_loading()
        self._btn_query.setEnabled(self._logged_in)
        self._btn_shortcut.setEnabled(self._logged_in)
        try:
            self._apply_query_result(df, err)
        except Exception as e:
            self._statusbar.showMessage(f"Errore: {e}", 10000)
            QMessageBox.warning(self, "Errore", str(e))

    def _apply_query_result(self, df: pd.DataFrame | None, err: str) -> None:
        if err:
            self._statusbar.showMessage(f"Errore: {err}", 10000)
            QMessageBox.warning(self, "Errore", err)
            return
        if df is None or df.empty:
            self._statusbar.showMessage("Nessun dato.", 5000)
            QMessageBox.information(self, "Risultato", "Nessun dato trovato.")
            return

        # Sort by Start Time descending (most recent first)
        time_col = None
        for c in df.columns:
            if "start time" in str(c).lower():
                time_col = c
                break
        if time_col:
            # utc=True avoids pandas 3.x "Mixed timezones detected" on DST / offset mixes
            df["_sort_ts"] = pd.to_datetime(df[time_col], errors="coerce", utc=True)
            df = df.sort_values("_sort_ts", ascending=False, na_position="last")
            df = df.drop(columns=["_sort_ts"]).reset_index(drop=True)

        self._current_df = df
        self._proxy.clear_filters()
        self._model.set_dataframe(df)
        self._compute_uniq()
        self._btn_export.setEnabled(True)
        self._lbl_filt.setText("")

        self._table.resizeColumnsToContents()
        h = self._table.horizontalHeader()
        for i in range(self._model.columnCount()):
            col_name = str(df.columns[i]) if i < len(df.columns) else ""
            if col_name in ("_download_url", "_unit_view"):
                self._table.setColumnHidden(i, True)
            else:
                w = h.sectionSize(i)
                h.resizeSection(i, max(min(w + 24, 320), 100))

        self._upd_count()
        if self._dashboard is not None:
            self._dashboard.update_data(self._current_df)
        self._statusbar.showMessage(f"Caricati {len(df)} record (piu' recenti prima).", 5000)

    # ── Shortcut persistence ──

    def _load_saved_shortcuts(self) -> None:
        self._saved_shortcuts: list[dict] = []
        if _SAVED_SHORTCUTS_FILE.exists():
            try:
                self._saved_shortcuts = json.loads(
                    _SAVED_SHORTCUTS_FILE.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                self._saved_shortcuts = []
        self._refresh_shortcut_combo()

    def _persist_shortcuts(self) -> None:
        _SAVED_SHORTCUTS_FILE.write_text(
            json.dumps(self._saved_shortcuts, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _refresh_shortcut_combo(self) -> None:
        current = self._cmb_shortcut.currentText()
        self._cmb_shortcut.clear()
        for sc in self._saved_shortcuts:
            label = sc.get("label", "")
            uuid = sc["uuid"]
            display = f"{label}  —  {uuid}" if label else uuid
            self._cmb_shortcut.addItem(display)
        self._cmb_shortcut.setCurrentText(current)

    @Slot()
    def _on_save_shortcut(self) -> None:
        text = self._cmb_shortcut.currentText().strip()
        if "  —  " in text:
            uuid = text.split("  —  ")[-1].strip()
        else:
            uuid = text
        if not uuid:
            QMessageBox.warning(self, "Salva shortcut", "Inserisci un UUID.")
            return

        label = self._txt_shortcut_label.text().strip()

        for sc in self._saved_shortcuts:
            if sc["uuid"] == uuid:
                sc["label"] = label
                self._persist_shortcuts()
                self._refresh_shortcut_combo()
                self._statusbar.showMessage(f"Shortcut aggiornato: {label or uuid}", 3000)
                return

        self._saved_shortcuts.append({"uuid": uuid, "label": label})
        self._persist_shortcuts()
        self._refresh_shortcut_combo()
        self._cmb_shortcut.setCurrentIndex(self._cmb_shortcut.count() - 1)
        self._txt_shortcut_label.clear()
        self._statusbar.showMessage(f"Shortcut salvato: {label or uuid}", 3000)

    @Slot()
    def _on_del_shortcut(self) -> None:
        idx = self._cmb_shortcut.currentIndex()
        if idx < 0 or idx >= len(self._saved_shortcuts):
            QMessageBox.warning(self, "Elimina shortcut",
                                "Seleziona uno shortcut salvato da eliminare.")
            return
        sc = self._saved_shortcuts[idx]
        name = sc.get("label") or sc["uuid"]
        reply = QMessageBox.question(
            self, "Conferma eliminazione",
            f"Eliminare lo shortcut \"{name}\"?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._saved_shortcuts.pop(idx)
            self._persist_shortcuts()
            self._refresh_shortcut_combo()
            self._statusbar.showMessage(f"Shortcut eliminato: {name}", 3000)

    # ── Date filters ──

    def _find_time_col(self) -> str | None:
        for c in self._current_df.columns:
            if "start time" in str(c).lower():
                return str(c)
        return None

    def _apply_date_filter(self) -> None:
        tc = self._find_time_col()
        if tc is None or self._current_df.empty:
            return
        d_from = self._date_from.date().toPython()
        d_to = self._date_to.date().toPython()

        from datetime import datetime
        times = pd.to_datetime(self._current_df[tc], errors="coerce", utc=True)
        dt_from = pd.Timestamp(datetime.combine(d_from, datetime.min.time()), tz="UTC")
        dt_to = pd.Timestamp(datetime.combine(d_to, datetime.max.time()), tz="UTC")

        mask = (times >= dt_from) & (times <= dt_to)
        filtered = self._current_df[mask].reset_index(drop=True)

        self._proxy.clear_filters()
        self._model.set_dataframe(filtered)
        self._compute_uniq()
        self._upd_count()
        self._statusbar.showMessage(
            f"Filtro date: {d_from} → {d_to}  ({len(filtered)} record)", 5000
        )

    def _clear_date_filter(self) -> None:
        if self._current_df.empty:
            return
        self._proxy.clear_filters()
        self._model.set_dataframe(self._current_df)
        self._compute_uniq()
        self._upd_count()
        self._lbl_filt.setText("")
        self._statusbar.showMessage(
            f"Filtro date rimosso ({len(self._current_df)} record)", 3000
        )

    def _quick_date_filter(self, days: int) -> None:
        today = QDate.currentDate()
        self._date_to.setDate(today)
        self._date_from.setDate(today.addDays(-days))
        self._apply_date_filter()

    def _compute_uniq(self) -> None:
        self._col_uniq.clear()
        for i, c in enumerate(self._current_df.columns):
            self._col_uniq[i] = sorted(
                self._current_df[c].fillna("").astype(str).unique().tolist()
            )

    # ── Header click → Excel filter ──

    @Slot(int)
    def _hdr_click(self, col: int) -> None:
        if col not in self._col_uniq:
            return
        name = str(self._model.headerData(col, Qt.Horizontal))
        active = self._proxy.get_active_filters()
        dlg = FilterDialog(name, self._col_uniq[col], active.get(col), self)
        if dlg.exec() == QDialog.Accepted:
            self._proxy.set_column_allowed(col, dlg.result_values)
            self._upd_count()
            self._upd_filt()

    def _upd_count(self) -> None:
        v, t = self._proxy.rowCount(), self._model.rowCount()
        base = f"{v} righe" if v == t else f"{v} di {t} righe"
        serials = self._count_visible_serials()
        if serials is not None:
            base += f"  \u2022  {serials} serial number"
        self._lbl_count.setText(base)
        self._maybe_refresh_dashboard()

    def _filtered_df(self) -> pd.DataFrame:
        """Return the visible data: model df (date-filtered) + grid filters."""
        df = self._model.dataframe
        if df.empty:
            return df
        af = self._proxy.get_active_filters()
        if not af:
            return df
        mask = pd.Series(True, index=df.index)
        for col, allowed in af.items():
            if col < len(df.columns):
                colname = df.columns[col]
                vals = df[colname].map(lambda x: "" if pd.isna(x) else str(x))
                mask &= vals.isin(allowed)
        return df[mask]

    def _maybe_refresh_dashboard(self) -> None:
        if self._dashboard is None:
            return
        if self._result_tabs.currentWidget() is self._dashboard:
            self._dashboard.update_data(self._filtered_df())

    @Slot(int)
    def _on_result_tab_changed(self, index: int) -> None:
        if index == self._dashboard_tab_index:
            self._ensure_dashboard()
        self._maybe_refresh_dashboard()

    def _serial_col_index(self) -> int | None:
        if self._current_df.empty:
            return None
        for i, c in enumerate(self._current_df.columns):
            if "serial" in str(c).lower():
                return i
        return None

    def _count_visible_serials(self) -> int | None:
        col = self._serial_col_index()
        if col is None:
            return None
        seen: set[str] = set()
        for r in range(self._proxy.rowCount()):
            src = self._proxy.mapToSource(self._proxy.index(r, col))
            val = self._model.data(src, Qt.DisplayRole)
            if val:
                seen.add(str(val))
        return len(seen)

    def _upd_filt(self) -> None:
        af = self._proxy.get_active_filters()
        if not af:
            self._lbl_filt.setText("")
            return
        parts = []
        for col, vals in af.items():
            n = str(self._model.headerData(col, Qt.Horizontal))
            parts.append(f"{n} ({len(vals)})")
        self._lbl_filt.setText("Filtri: " + " | ".join(parts))

    @Slot()
    def _on_clear(self) -> None:
        self._proxy.clear_filters()
        self._lbl_filt.setText("")
        self._upd_count()

    # ── Document download ──

    @Slot(QModelIndex)
    def _on_cell_click(self, proxy_idx: QModelIndex) -> None:
        src = self._proxy.mapToSource(proxy_idx)
        col_name = str(self._model.headerData(src.column(), Qt.Horizontal))
        if col_name != "Documents":
            return
        url = self._model.get_download_url(src.row())
        if url:
            self._download_documents(url, src.row())

    _download_finished = Signal(str, str)

    def _download_documents(self, url: str, row: int) -> None:
        if self._downloading:
            return

        serial = ""
        for c in self._current_df.columns:
            if "serial" in str(c).lower():
                val = self._current_df.iat[row, self._current_df.columns.get_loc(c)]
                serial = str(val) if not pd.isna(val) else ""
                break

        filename_hint = f"documents_{serial}.zip"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Salva documenti", filename_hint, "ZIP (*.zip);;Tutti (*)"
        )
        if not save_path:
            return

        self._downloading = True
        self._overlay.show_loading(f"Download documenti {serial}…")

        def _do_download():
            try:
                resp = self._get_client().session.get(url, timeout=120, stream=True)
                resp.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                self._download_finished.emit(save_path, "")
            except Exception as e:
                self._download_finished.emit("", str(e))

        threading.Thread(target=_do_download, daemon=True).start()

    @Slot(str, str)
    def _on_download_finished(self, path: str, err: str) -> None:
        self._downloading = False
        self._overlay.hide_loading()
        if err:
            QMessageBox.warning(self, "Errore download", err)
            self._statusbar.showMessage(f"Errore download: {err}", 5000)
        else:
            self._statusbar.showMessage(f"Documenti salvati: {path}", 5000)

    # ── Unit Results View ──

    _unit_view_done = Signal(str, str)

    def _open_unit_view(self, unit_view: str) -> None:
        if self._downloading:
            return
        self._downloading = True
        self._overlay.show_loading("Apertura Unit Results View…")

        def _do_open():
            try:
                url = self._get_client().open_unit_view(unit_view)
                self._unit_view_done.emit(url, "")
            except Exception as e:
                self._unit_view_done.emit("", str(e))

        threading.Thread(target=_do_open, daemon=True).start()

    @Slot(str, str)
    def _on_unit_view_done(self, url: str, err: str) -> None:
        self._downloading = False
        self._overlay.hide_loading()
        if err:
            QMessageBox.warning(self, "Errore Unit Results View", err)
            self._statusbar.showMessage(f"Errore Unit Results View: {err}", 5000)
        else:
            self._statusbar.showMessage("Unit Results View aperto nel browser.", 5000)

    # ── Context menu ──

    @Slot()
    def _ctx_menu(self, pos) -> None:
        idx = self._table.indexAt(pos)
        if not idx.isValid():
            return
        src = self._proxy.mapToSource(idx)
        cell = str(self._model.data(src, Qt.DisplayRole) or "")
        col = src.column()
        cn = str(self._model.headerData(col, Qt.Horizontal))

        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background:white; color:#212121; border:1px solid #bdbdbd; }"
            "QMenu::item:selected { background:#e3f2fd; color:#212121; }"
        )
        a1 = menu.addAction("Copia cella")
        a2 = menu.addAction("Copia riga")
        menu.addSeparator()
        a3 = menu.addAction(f'Mostra solo "{cell}"')
        a4 = menu.addAction(f'Escludi "{cell}"')
        menu.addSeparator()
        a5 = menu.addAction(f'Filtro Excel su "{cn}"...')

        dl_url = self._model.get_download_url(src.row())
        a_dl = None
        if dl_url:
            menu.addSeparator()
            a_dl = menu.addAction("Scarica documenti")

        unit_view = self._model.get_unit_view(src.row())
        a_uv = None
        if unit_view:
            if not dl_url:
                menu.addSeparator()
            a_uv = menu.addAction("Apri Unit Results View")

        a = menu.exec(self._table.viewport().mapToGlobal(pos))
        if a == a_dl and dl_url:
            self._download_documents(dl_url, src.row())
        elif a == a_uv and unit_view:
            self._open_unit_view(unit_view)
        elif a == a1:
            QApplication.clipboard().setText(cell)
        elif a == a2:
            r = src.row()
            vs = [str(self._model.data(self._model.index(r, c), Qt.DisplayRole) or "")
                  for c in range(self._model.columnCount())]
            QApplication.clipboard().setText("\t".join(vs))
        elif a == a3:
            self._proxy.set_column_allowed(col, {cell})
            self._upd_count(); self._upd_filt()
        elif a == a4:
            cur = self._proxy.get_active_filters().get(col)
            if cur is None:
                cur = set(self._col_uniq.get(col, []))
            cur.discard(cell)
            self._proxy.set_column_allowed(col, cur)
            self._upd_count(); self._upd_filt()
        elif a == a5:
            self._hdr_click(col)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_overlay"):
            self._overlay.resize(self.centralWidget().size())

    def closeEvent(self, event) -> None:
        if self._client is not None:
            self._client.close()
        super().closeEvent(event)

    # ── Export ──

    @Slot()
    def _on_export(self) -> None:
        if self._current_df.empty:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Esporta CSV", "", "CSV (*.csv)")
        if not path:
            return
        rows = [self._proxy.mapToSource(self._proxy.index(r, 0)).row()
                for r in range(self._proxy.rowCount())]
        out = self._current_df.iloc[rows]
        out.to_csv(path, index=False, encoding="utf-8-sig")
        self._statusbar.showMessage(f"Esportate {len(out)} righe → {path}", 5000)


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    splash = _STARTUP_SPLASH
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    app.setFont(QFont(FONT_FAMILY, 10))
    win = MainWindow()
    if splash is not None:
        splash.finish(win)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
