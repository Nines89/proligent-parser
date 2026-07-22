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

import io
import importlib.util
import json
import re
import threading
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
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
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QFont,
    QPainter,
    QPen,
    QPixmap,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QCheckBox,
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

_SAVED_SHORTCUTS_FILE = Path(__file__).parent / "saved_shortcuts.json"
_SAVED_WAREHOUSE_FILE = Path(__file__).parent / "saved_warehouse_queries.json"

from automations_lib import (
    create_automation,
    delete_automation,
    ensure_dirs,
    list_automations,
    list_plot_images,
)

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
# New automation dialog
# ---------------------------------------------------------------------------

class NewAutomationDialog(QDialog):
    """Ask for automation name and optional bulk document download."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nuova automazione")
        self.setMinimumWidth(460)
        self.setStyleSheet("background:#fafafa; color:#212121;")

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        lbl = QLabel("Nome dell'automazione")
        lbl.setStyleSheet("font-size:13px; color:#424242;")
        lay.addWidget(lbl)

        self._name = QLineEdit()
        self._name.setPlaceholderText("es. Analisi yield")
        self._name.setStyleSheet(
            "font-size:14px; padding:8px; color:#212121; background:white;"
        )
        lay.addWidget(self._name)

        self._chk_download = QCheckBox(
            "Scarica i file per tutti i report del DataFrame filtrato"
        )
        self._chk_download.setStyleSheet("font-size:13px; color:#424242;")
        self._chk_download.setToolTip(
            "Se attivo, dopo la creazione vengono scaricati in files/ "
            "tutti i documenti collegati alle righe visibili in Dati."
        )
        lay.addWidget(self._chk_download)

        hint = QLabel(
            "I file finiscono in automations/<nome>/files/. "
            "Serve Login Proligent se i link sono da Shortcut / report web."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("font-size:11px; color:#9e9e9e;")
        lay.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

        self._name.setFocus()

    def automation_name(self) -> str:
        return self._name.text().strip()

    def download_documents(self) -> bool:
        return self._chk_download.isChecked()


# ---------------------------------------------------------------------------
# Bulk document download progress
# ---------------------------------------------------------------------------

class BulkDownloadDialog(QDialog):
    """Progress UI for downloading many report documents."""

    def __init__(
        self,
        total: int,
        dest: Path,
        parent=None,
        *,
        cancel_event: threading.Event | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Download documenti")
        self.setMinimumWidth(520)
        self.setModal(True)
        self.setStyleSheet("background:#fafafa; color:#212121;")
        self._cancelled = False
        self._cancel_event = cancel_event
        self._total = max(total, 1)
        self._t0 = time.monotonic()

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        self._lbl_title = QLabel(f"Download di {total} documenti…")
        self._lbl_title.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#1565c0;"
        )
        lay.addWidget(self._lbl_title)

        self._lbl_dest = QLabel(f"Destinazione: {dest}")
        self._lbl_dest.setWordWrap(True)
        self._lbl_dest.setStyleSheet("font-size:11px; color:#9e9e9e;")
        self._lbl_dest.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self._lbl_dest)

        self._bar = QProgressBar()
        self._bar.setRange(0, total)
        self._bar.setValue(0)
        self._bar.setTextVisible(True)
        self._bar.setFormat("%v / %m")
        self._bar.setStyleSheet(
            "QProgressBar { border:1px solid #bdbdbd; border-radius:4px;"
            " background:white; height:22px; text-align:center; }"
            "QProgressBar::chunk { background:#1565c0; border-radius:3px; }"
        )
        lay.addWidget(self._bar)

        self._lbl_status = QLabel("Preparazione…")
        self._lbl_status.setWordWrap(True)
        self._lbl_status.setStyleSheet("font-size:13px; color:#424242;")
        lay.addWidget(self._lbl_status)

        self._lbl_eta = QLabel("Tempo rimanente: calcolo…")
        self._lbl_eta.setStyleSheet("font-size:12px; color:#616161;")
        lay.addWidget(self._lbl_eta)

        self._lbl_stats = QLabel("Completati: 0  ·  Errori: 0")
        self._lbl_stats.setStyleSheet("font-size:12px; color:#616161;")
        lay.addWidget(self._lbl_stats)

        btns = QDialogButtonBox()
        self._btn_cancel = btns.addButton(QDialogButtonBox.Cancel)
        self._btn_cancel.clicked.connect(self._on_cancel)
        lay.addWidget(btns)
        self._btns = btns

    def _on_cancel(self) -> None:
        self._cancelled = True
        if self._cancel_event is not None:
            self._cancel_event.set()
        self._lbl_status.setText("Annullamento in corso (al termine del file attuale)…")
        self._btn_cancel.setEnabled(False)

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        if seconds < 0 or seconds != seconds:  # NaN
            return "—"
        s = int(round(seconds))
        if s < 60:
            return f"{s}s"
        m, s = divmod(s, 60)
        if m < 60:
            return f"{m}m {s:02d}s"
        h, m = divmod(m, 60)
        return f"{h}h {m:02d}m"

    def update_progress(
        self,
        done: int,
        total: int,
        *,
        current: str = "",
        ok: int = 0,
        failed: int = 0,
        eta_seconds: float | None = None,
    ) -> None:
        self._bar.setMaximum(max(total, 1))
        self._bar.setValue(min(done, total))
        elapsed = time.monotonic() - self._t0
        if current:
            self._lbl_status.setText(f"Scaricando: {current}")
        self._lbl_stats.setText(
            f"Completati: {ok}  ·  Errori: {failed}  ·  "
            f"Trascorsi: {self._fmt_duration(elapsed)}"
        )
        if eta_seconds is None:
            self._lbl_eta.setText("Tempo rimanente: calcolo…")
        else:
            self._lbl_eta.setText(
                f"Tempo rimanente: {self._fmt_duration(eta_seconds)}"
            )

    def mark_finished(self, ok: int, failed: int, cancelled: bool) -> None:
        elapsed = time.monotonic() - self._t0
        self._bar.setValue(self._bar.maximum())
        if cancelled:
            self._lbl_title.setText("Download interrotto")
            self._lbl_status.setText(
                f"Annullato dall'utente dopo {ok + failed} file."
            )
        elif failed:
            self._lbl_title.setText("Download completato con errori")
            self._lbl_status.setText(
                f"Salvati {ok} file, {failed} errori."
            )
        else:
            self._lbl_title.setText("Download completato")
            self._lbl_status.setText(f"Tutti i {ok} file sono stati salvati.")
        self._lbl_eta.setText(f"Tempo totale: {self._fmt_duration(elapsed)}")
        self._lbl_stats.setText(f"Completati: {ok}  ·  Errori: {failed}")
        self._btns.clear()
        close_btn = self._btns.addButton(QDialogButtonBox.Ok)
        close_btn.clicked.connect(self.accept)


# ---------------------------------------------------------------------------
# Automation plot thumbnail
# ---------------------------------------------------------------------------

class ClickablePlotLabel(QLabel):
    """Thumbnail that opens the image file on double-click."""

    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        self._path = Path(path)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"Doppio click per aprire:\n{self._path}")
        self.setStyleSheet(
            "QLabel { background:white; border:1px solid #bdbdbd;"
            " border-radius:4px; padding:4px; }"
        )
        pix = QPixmap(str(self._path))
        if not pix.isNull():
            self.setPixmap(
                pix.scaled(280, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.setText(self._path.name)
            self.setMinimumSize(160, 100)

    def mouseDoubleClickEvent(self, event) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._path.resolve())))
        super().mouseDoubleClickEvent(event)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):

    _login_done = Signal(bool, str)
    _query_done = Signal(object, str)
    _progress_msg = Signal(str)
    _bulk_dl_progress = Signal(int, int, str, int, int, float)
    _bulk_dl_finished = Signal(int, int, bool)
    # slug, stdout, stderr, traceback, new_image_paths (list[str])
    _automation_run_done = Signal(str, str, str, str, object)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Proligent Parser")
        self.resize(1500, 900)

        self._client = None
        self._wh_client = None
        self._logged_in = False
        self._wh_connected = False
        self._downloading = False
        self._bulk_dlg: BulkDownloadDialog | None = None
        self._bulk_cancel = threading.Event()
        self._current_df = pd.DataFrame()
        self._col_uniq: dict[int, list[str]] = {}
        self._meas_names: list[str] = []
        self._meas_col_idx: int | None = None
        self._last_result_tab = 0
        # slug -> automation info (tabs are discovered from automations/* folders)
        self._automation_tabs: dict[str, dict[str, Any]] = {}

        self._build_ui()
        self._overlay = LoadingOverlay(self.centralWidget())
        self._load_existing_automations()
        self._connect()
        ensure_dirs()

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

        # Tab: Warehouse DB (proligent_db_sdk / SQL)
        t3 = QWidget()
        v3 = QVBoxLayout(t3)
        v3.setContentsMargins(12, 12, 12, 8)
        v3.setSpacing(8)

        # Saved warehouse searches row
        wh_saved_row = QHBoxLayout()
        wh_saved_row.setSpacing(10)
        lbl_wh_saved = QLabel("Ricerche salvate:")
        lbl_wh_saved.setStyleSheet("font-size:13px; color:#424242;")
        wh_saved_row.addWidget(lbl_wh_saved)

        self._cmb_wh_saved = QComboBox()
        self._cmb_wh_saved.setEditable(False)
        self._cmb_wh_saved.setStyleSheet(
            "font-size:13px; padding:6px 8px; color:#212121; background:white;"
        )
        self._cmb_wh_saved.setMinimumWidth(320)
        wh_saved_row.addWidget(self._cmb_wh_saved, stretch=1)

        self._txt_wh_label = QLineEdit()
        self._txt_wh_label.setPlaceholderText("Nome ricerca (opzionale)")
        self._txt_wh_label.setStyleSheet(
            "font-size:13px; padding:4px 6px; color:#212121; background:white;"
        )
        wh_saved_row.addWidget(self._txt_wh_label, stretch=1)

        self._btn_wh_save = QPushButton("  Salva  ")
        self._btn_wh_save.setStyleSheet(
            "font-size:12px; font-weight:bold; padding:5px 18px;"
            "background:#2e7d32; color:white; border:none; border-radius:3px;"
        )
        wh_saved_row.addWidget(self._btn_wh_save)

        self._btn_wh_del = QPushButton("  Elimina  ")
        self._btn_wh_del.setStyleSheet(
            "font-size:12px; font-weight:bold; padding:5px 18px;"
            "background:#c62828; color:white; border:none; border-radius:3px;"
        )
        wh_saved_row.addWidget(self._btn_wh_del)
        v3.addLayout(wh_saved_row)

        g3 = QGridLayout()
        g3.setSpacing(8)
        v3.addLayout(g3)

        self._cmb_wh_type = QComboBox()
        self._cmb_wh_type.addItems(["Operation runs (+ docs)", "Measurements"])
        self._txt_wh_product = QLineEdit()
        self._txt_wh_product.setPlaceholderText("es. 3TL04228AA")
        self._txt_wh_serial = QLineEdit()
        self._txt_wh_serial.setPlaceholderText("serial number")
        self._txt_wh_operation = QLineEdit()
        self._txt_wh_operation.setPlaceholderText("es. 08000 - FUNCTIONAL TEST")
        self._txt_wh_station = QLineEdit()
        self._txt_wh_station.setPlaceholderText("location / station (partial OK)")
        self._txt_wh_operator = QLineEdit()
        self._txt_wh_operator.setPlaceholderText("operator id / name (partial OK)")
        self._txt_wh_measurement = QLineEdit()
        self._txt_wh_measurement.setPlaceholderText("MeasurementName (solo Measurements)")
        self._cmb_wh_status = QComboBox()
        self._cmb_wh_status.addItems(["(tutti)", "PASS", "FAIL", "ABORTED"])
        self._spn_wh_top = QSpinBox()
        self._spn_wh_top.setRange(0, 500_000)
        self._spn_wh_top.setValue(10_000)
        self._spn_wh_top.setSpecialValueText("Illimitato")

        _WH_FIELD_CSS = (
            "font-size:13px; padding:4px 6px; color:#212121; background:white;"
        )
        for w in (
            self._cmb_wh_type, self._txt_wh_product, self._txt_wh_serial,
            self._txt_wh_operation, self._txt_wh_station, self._txt_wh_operator,
            self._txt_wh_measurement, self._cmb_wh_status, self._spn_wh_top,
        ):
            w.setStyleSheet(_WH_FIELD_CSS)

        self._date_wh_from = QDateEdit()
        self._date_wh_from.setCalendarPopup(True)
        self._date_wh_from.setDisplayFormat("yyyy-MM-dd")
        self._date_wh_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_wh_to = QDateEdit()
        self._date_wh_to.setCalendarPopup(True)
        self._date_wh_to.setDisplayFormat("yyyy-MM-dd")
        self._date_wh_to.setDate(QDate.currentDate())
        self._chk_wh_dates = QCheckBox("Filtra per data")
        self._chk_wh_dates.setChecked(False)
        self._chk_wh_dates.setStyleSheet("font-size:12px; color:#424242;")
        self._date_wh_from.setEnabled(False)
        self._date_wh_to.setEnabled(False)

        wh_fields = [
            (0, 0, "Tipo:", self._cmb_wh_type),
            (0, 2, "Prodotto:", self._txt_wh_product),
            (0, 4, "Serial:", self._txt_wh_serial),
            (0, 6, "Operazione:", self._txt_wh_operation),
            (1, 0, "Stazione:", self._txt_wh_station),
            (1, 2, "Operatore:", self._txt_wh_operator),
            (1, 4, "Status:", self._cmb_wh_status),
            (1, 6, "Max righe:", self._spn_wh_top),
            (2, 2, "Data da:", self._date_wh_from),
            (2, 4, "Data a:", self._date_wh_to),
            (3, 4, "Meas.Name:", self._txt_wh_measurement),
        ]
        for row, col, label, widget in wh_fields:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size:13px; color:#424242;")
            g3.addWidget(lbl, row, col)
            g3.addWidget(widget, row, col + 1)

        g3.addWidget(self._chk_wh_dates, 2, 0, 1, 2)

        self._chk_wh_latest = QCheckBox("Solo ultimo passaggio per serial")
        self._chk_wh_latest.setStyleSheet("font-size:12px; color:#424242;")
        g3.addWidget(self._chk_wh_latest, 3, 0, 1, 2)

        self._chk_wh_product_like = QCheckBox("Prodotto LIKE")
        self._chk_wh_product_like.setChecked(True)
        self._chk_wh_product_like.setStyleSheet("font-size:12px; color:#424242;")
        g3.addWidget(self._chk_wh_product_like, 3, 2, 1, 2)

        wh_btn_col = QVBoxLayout()
        self._btn_wh_connect = QPushButton("  Connetti DB  ")
        self._btn_wh_connect.setStyleSheet(
            "font-size:13px; font-weight:bold; padding:8px 18px;"
            "background:#1565c0; color:white; border:none; border-radius:4px;"
        )
        self._btn_wh_query = QPushButton("  Esegui Warehouse  ")
        self._btn_wh_query.setEnabled(False)
        self._btn_wh_query.setStyleSheet(
            "font-size:14px; font-weight:bold; padding:12px 22px;"
            "background:#2e7d32; color:white; border:none; border-radius:4px;"
        )
        wh_btn_col.addWidget(self._btn_wh_connect)
        wh_btn_col.addWidget(self._btn_wh_query)
        wh_btn_col.addStretch()
        g3.addLayout(wh_btn_col, 0, 8, 4, 1)

        self._lbl_wh_status = QLabel("  Warehouse: non connesso (Windows auth)")
        self._lbl_wh_status.setStyleSheet("font-size:12px; color:#757575;")
        v3.addWidget(self._lbl_wh_status)

        wh_hint = QLabel(
            "Query diretta sul data warehouse SQL — ideale per migliaia di righe. "
            "Salva le combinazioni di filtri per riutilizzarle. "
            "Di default non si applica filtro date (tutte le date disponibili)."
        )
        wh_hint.setStyleSheet("font-size:12px; color:#9e9e9e; font-style:italic;")
        wh_hint.setWordWrap(True)
        v3.addWidget(wh_hint)

        self._tabs.addTab(t3, "  Warehouse DB  ")
        self._tabs.tabBar().setVisible(self._tabs.count() > 1)

        self._load_saved_shortcuts()
        self._load_saved_warehouse_queries()

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

        # ── Toolbar: MeasurementName (enabled only after a search with that column) ──
        meas_row = QHBoxLayout()
        meas_row.setSpacing(6)
        lbl_meas = QLabel("MeasurementName:")
        lbl_meas.setStyleSheet("font-size:12px; color:#424242;")
        meas_row.addWidget(lbl_meas)

        self._cmb_meas_name = QComboBox()
        self._cmb_meas_name.setEditable(True)
        self._cmb_meas_name.setInsertPolicy(QComboBox.NoInsert)
        self._cmb_meas_name.setEnabled(False)
        self._cmb_meas_name.setMinimumWidth(320)
        self._cmb_meas_name.addItem("(tutti)")
        self._cmb_meas_name.lineEdit().setPlaceholderText(
            "Disponibile dopo una ricerca Measurements"
        )
        self._cmb_meas_name.setStyleSheet(
            "font-size:12px; padding:4px 6px; color:#212121; background:white;"
        )
        meas_row.addWidget(self._cmb_meas_name, stretch=1)

        self._btn_meas_multi = QPushButton("Seleziona…")
        self._btn_meas_multi.setEnabled(False)
        self._btn_meas_multi.setToolTip(
            "Scegli uno o più MeasurementName tra quelli letti dalla query"
        )
        self._btn_meas_multi.setStyleSheet(
            "font-size:11px; padding:4px 10px; color:#212121; background:#e3f2fd;"
            " border:1px solid #90caf9; border-radius:3px;"
        )
        meas_row.addWidget(self._btn_meas_multi)

        self._btn_meas_clear = QPushButton("Tutti i meas.")
        self._btn_meas_clear.setEnabled(False)
        self._btn_meas_clear.setStyleSheet(
            "font-size:11px; padding:4px 10px; color:#424242; background:#e0e0e0;"
            " border:1px solid #bdbdbd; border-radius:3px;"
        )
        meas_row.addWidget(self._btn_meas_clear)

        self._lbl_meas_info = QLabel("")
        self._lbl_meas_info.setStyleSheet("font-size:11px; color:#9e9e9e;")
        meas_row.addWidget(self._lbl_meas_info)
        meas_row.addStretch()
        root.addLayout(meas_row)

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

        # "+" tab: create a custom automation (always last)
        self._add_tab_placeholder = QWidget()
        self._add_tab_index = self._result_tabs.addTab(
            self._add_tab_placeholder, "  +  "
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
        self._btn_wh_connect.clicked.connect(self._on_wh_connect)
        self._btn_wh_query.clicked.connect(self._on_wh_query)
        self._btn_wh_save.clicked.connect(self._on_save_warehouse_query)
        self._btn_wh_del.clicked.connect(self._on_del_warehouse_query)
        self._cmb_wh_saved.currentIndexChanged.connect(self._on_wh_saved_selected)
        self._chk_wh_dates.toggled.connect(self._on_wh_dates_toggled)
        self._btn_save_sc.clicked.connect(self._on_save_shortcut)
        self._btn_del_sc.clicked.connect(self._on_del_shortcut)
        self._btn_export.clicked.connect(self._on_export)
        self._btn_clear.clicked.connect(self._on_clear)
        self._btn_apply_date.clicked.connect(self._apply_date_filter)
        self._btn_clear_date.clicked.connect(self._clear_date_filter)
        self._btn_24h.clicked.connect(lambda: self._quick_date_filter(1))
        self._btn_7d.clicked.connect(lambda: self._quick_date_filter(7))
        self._btn_30d.clicked.connect(lambda: self._quick_date_filter(30))
        self._cmb_meas_name.currentTextChanged.connect(self._on_meas_name_combo)
        self._btn_meas_multi.clicked.connect(self._on_meas_name_multi)
        self._btn_meas_clear.clicked.connect(self._clear_meas_name_filter)
        self._login_done.connect(self._login_result)
        self._query_done.connect(self._query_result)
        self._progress_msg.connect(self._overlay.set_message)
        self._download_finished.connect(self._on_download_finished)
        self._unit_view_done.connect(self._on_unit_view_done)
        self._bulk_dl_progress.connect(self._on_bulk_dl_progress)
        self._bulk_dl_finished.connect(self._on_bulk_dl_finished)
        self._automation_run_done.connect(self._on_automation_run_done)
        self._table.horizontalHeader().sectionClicked.connect(self._hdr_click)
        self._table.clicked.connect(self._on_cell_click)
        self._table.customContextMenuRequested.connect(self._ctx_menu)
        self._result_tabs.currentChanged.connect(self._on_result_tab_changed)

    def _get_client(self):
        if self._client is None:
            from proligent_client import ProligentClient
            self._client = ProligentClient()
        return self._client

    def _get_wh_client(self):
        if self._wh_client is None:
            from warehouse_client import WarehouseClient
            self._wh_client = WarehouseClient()
        return self._wh_client

    def _set_query_buttons_enabled(self, enabled: bool) -> None:
        self._btn_query.setEnabled(enabled and self._logged_in)
        self._btn_shortcut.setEnabled(enabled and self._logged_in)
        self._btn_wh_query.setEnabled(enabled and self._wh_connected)
        self._btn_wh_connect.setEnabled(enabled)

    def _ensure_dashboard(self) -> None:
        if self._dashboard is not None:
            return
        from gui_dashboard import DashboardWidget

        self._dashboard = DashboardWidget()
        self._result_tabs.removeTab(self._dashboard_tab_index)
        self._result_tabs.insertTab(
            self._dashboard_tab_index, self._dashboard, "  Dashboard  "
        )

    def _sync_add_tab_index(self) -> None:
        """Keep the '+' tab as the last result tab."""
        self._add_tab_index = self._result_tabs.count() - 1

    @Slot()
    def _on_add_automation(self) -> None:
        dlg = NewAutomationDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        name = dlg.automation_name()
        want_download = dlg.download_documents()
        if not name:
            QMessageBox.warning(
                self, "Nuova automazione", "Inserisci un nome per l'automazione."
            )
            return
        try:
            info = create_automation(name, download_documents=want_download)
        except ValueError as e:
            QMessageBox.warning(self, "Nuova automazione", str(e))
            return
        except OSError as e:
            QMessageBox.critical(
                self, "Nuova automazione", f"Impossibile creare l'automazione:\n{e}"
            )
            return

        self._open_automation_tab(info, select=True, announce=True)

        if want_download:
            self._start_automation_document_download(info)

    def _collect_document_jobs(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Build download jobs from rows that have a document URL."""
        if df is None or df.empty or "_download_url" not in df.columns:
            return []

        serial_col = None
        for c in df.columns:
            if "serial" in str(c).lower():
                serial_col = c
                break

        file_col = None
        for preferred in ("file name", "filename", "name"):
            for c in df.columns:
                if str(c).lower() == preferred:
                    file_col = c
                    break
            if file_col is not None:
                break

        jobs: list[dict[str, Any]] = []
        for pos in range(len(df)):
            url = df["_download_url"].iat[pos]
            if pd.isna(url):
                continue
            url = str(url).strip()
            if not url or url.lower() in ("nan", "none", "0"):
                continue

            serial = ""
            if serial_col is not None:
                val = df[serial_col].iat[pos]
                if not pd.isna(val):
                    serial = str(val).strip()

            file_hint = ""
            if file_col is not None:
                val = df[file_col].iat[pos]
                if not pd.isna(val):
                    text = str(val).strip()
                    if text and text.lower() not in ("download", "0", "nan"):
                        file_hint = text

            jobs.append({
                "url": url,
                "serial": serial,
                "file_hint": file_hint,
                "index": pos,
            })
        return jobs

    @staticmethod
    def _safe_filename(text: str, fallback: str = "document") -> str:
        text = (text or "").strip()
        text = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", text)
        text = re.sub(r"\s+", "_", text).strip("._")
        return (text[:120] if text else fallback) or fallback

    def _expected_document_name(self, job: dict[str, Any], url: str) -> str:
        from warehouse_client import is_direct_document_url

        if job.get("file_hint"):
            base = self._safe_filename(str(job["file_hint"]))
        elif job.get("serial"):
            base = self._safe_filename(f"documents_{job['serial']}")
        else:
            base = f"document_{job['index'] + 1}"

        if "." not in Path(base).name:
            if is_direct_document_url(url):
                base += ".bin"
            else:
                base += ".zip"
        return base

    def _job_save_path(self, dest: Path, job: dict[str, Any], url: str) -> Path:
        """Canonical path for a document (no _2/_3 suffixes)."""
        return Path(dest) / self._expected_document_name(job, url)

    def _document_already_present(
        self, dest: Path, job: dict[str, Any], url: str
    ) -> bool:
        """True if files_dir already has this report (exact name or same stem)."""
        dest = Path(dest)
        if not dest.is_dir():
            return False
        expected = self._expected_document_name(job, url)
        if (dest / expected).is_file():
            return True
        stem = Path(expected).stem.lower()
        serial = str(job.get("serial") or "").strip().lower()
        for p in dest.iterdir():
            if not p.is_file():
                continue
            name = p.name.lower()
            pstem = p.stem.lower()
            if pstem == stem or pstem.startswith(stem + "_"):
                return True
            if serial and serial in name:
                return True
        return False

    def _start_automation_document_download(
        self,
        info: dict[str, Any],
        *,
        only_missing: bool = False,
    ) -> None:
        if self._downloading:
            QMessageBox.information(
                self,
                "Download in corso",
                "C'è già un download attivo. Riprova al termine.",
            )
            return

        df = self._filtered_df()
        jobs = self._collect_document_jobs(df)
        dest = Path(info["files_dir"])
        dest.mkdir(parents=True, exist_ok=True)

        if only_missing:
            jobs = [
                j for j in jobs
                if not self._document_already_present(dest, j, j["url"])
            ]

        if not jobs:
            if only_missing:
                QMessageBox.information(
                    self,
                    "Upload",
                    "Nessun file nuovo da scaricare: "
                    "tutti i documenti del DataFrame filtrato "
                    "sono già presenti in files/.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "Nessun documento",
                    "Nel DataFrame filtrato non ci sono link documento da scaricare.\n"
                    "Carica una ricerca Operation runs (con Documents) e riprova.",
                )
            return

        from warehouse_client import is_direct_document_url

        needs_web = any(not is_direct_document_url(j["url"]) for j in jobs)
        if needs_web and not self._logged_in:
            QMessageBox.warning(
                self,
                "Login richiesto",
                "Alcuni documenti richiedono Login Proligent "
                "(Shortcut / report web). Effettua il login e riprova.",
            )
            return

        self._bulk_cancel.clear()
        self._bulk_dlg = BulkDownloadDialog(
            len(jobs), dest, self, cancel_event=self._bulk_cancel
        )
        self._downloading = True

        def _do_bulk() -> None:
            from warehouse_client import download_url_to_file, is_direct_document_url

            ok = 0
            failed = 0
            durations: list[float] = []
            cancelled = False
            session = None
            try:
                if needs_web:
                    session = self._get_client().session
            except Exception as e:
                self._bulk_dl_finished.emit(0, len(jobs), False)
                self._statusbar.showMessage(f"Errore sessione download: {e}", 8000)
                return

            for i, job in enumerate(jobs):
                if self._bulk_cancel.is_set():
                    cancelled = True
                    break
                url = job["url"]
                label = job.get("serial") or job.get("file_hint") or f"#{job['index'] + 1}"
                eta = (
                    (sum(durations) / len(durations)) * (len(jobs) - i)
                    if durations
                    else -1.0
                )
                self._bulk_dl_progress.emit(
                    i, len(jobs), str(label), ok, failed, eta
                )
                save_path = self._job_save_path(dest, job, url)
                if save_path.exists():
                    ok += 1
                    self._bulk_dl_progress.emit(
                        i + 1, len(jobs), str(label), ok, failed, eta
                    )
                    continue
                t0 = time.monotonic()
                try:
                    use_session = None if is_direct_document_url(url) else session
                    download_url_to_file(url, str(save_path), session=use_session)
                    ok += 1
                except Exception:
                    failed += 1
                durations.append(time.monotonic() - t0)
                eta_after = (
                    (sum(durations) / len(durations)) * (len(jobs) - i - 1)
                    if durations
                    else -1.0
                )
                self._bulk_dl_progress.emit(
                    i + 1, len(jobs), str(label), ok, failed, eta_after
                )

            self._bulk_dl_finished.emit(ok, failed, cancelled)

        threading.Thread(target=_do_bulk, daemon=True).start()
        self._bulk_dlg.exec()
        self._bulk_dlg = None

    @Slot(int, int, str, int, int, float)
    def _on_bulk_dl_progress(
        self,
        done: int,
        total: int,
        current: str,
        ok: int,
        failed: int,
        eta: float,
    ) -> None:
        if self._bulk_dlg is None:
            return
        self._bulk_dlg.update_progress(
            done,
            total,
            current=current,
            ok=ok,
            failed=failed,
            eta_seconds=None if eta < 0 else eta,
        )

    @Slot(int, int, bool)
    def _on_bulk_dl_finished(self, ok: int, failed: int, cancelled: bool) -> None:
        self._downloading = False
        if self._bulk_dlg is not None:
            self._bulk_dlg.mark_finished(ok, failed, cancelled)
        if cancelled:
            msg = f"Download interrotto: {ok} salvati, {failed} errori"
        elif failed:
            msg = f"Download finito: {ok} salvati, {failed} errori"
        else:
            msg = f"Download completato: {ok} file salvati"
        self._statusbar.showMessage(msg, 8000)

    def _load_existing_automations(self) -> None:
        """Open one result tab for every folder under automations/."""
        loaded = list_automations()
        for info in loaded:
            self._open_automation_tab(info, select=False, announce=False)
        if loaded:
            names = ", ".join(i["name"] for i in loaded)
            self._statusbar.showMessage(
                f"Automazioni caricate ({len(loaded)}): {names}", 8000
            )

    def _open_automation_tab(
        self,
        info: dict[str, Any],
        *,
        select: bool = True,
        announce: bool = False,
    ) -> None:
        name = info["name"]
        slug = str(info["slug"])
        script_path: Path = info["script"]
        root: Path = info["root"]
        download_docs = bool(info.get("download_documents", False))

        if slug in self._automation_tabs:
            if select:
                idx = self._result_tabs.indexOf(self._automation_tabs[slug]["widget"])
                if idx >= 0:
                    self._result_tabs.setCurrentIndex(idx)
            return

        tab = QWidget()
        tab.setProperty("automation_slug", slug)
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        title = QLabel(name)
        title.setStyleSheet(
            "font-size:18px; font-weight:bold; color:#1565c0;"
        )
        lay.addWidget(title)

        detail = QLabel(
            f"Cartella: {root}\n"
            f"Script:   {script_path}"
        )
        detail.setWordWrap(True)
        detail.setStyleSheet("font-size:12px; color:#9e9e9e;")
        detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(detail)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_run = QPushButton("  Run  ")
        btn_run.setStyleSheet(
            "font-size:13px; font-weight:bold; padding:8px 22px;"
            "background:#2e7d32; color:white; border:none; border-radius:4px;"
        )
        btn_run.setToolTip("Esegue run(df, files_dir) sullo script main.py")
        btn_run.clicked.connect(lambda: self._on_automation_run(slug))
        btn_row.addWidget(btn_run)

        btn_upload = None
        if download_docs:
            btn_upload = QPushButton("  Upload  ")
            btn_upload.setStyleSheet(
                "font-size:13px; font-weight:bold; padding:8px 22px;"
                "background:#1565c0; color:white; border:none; border-radius:4px;"
            )
            btn_upload.setToolTip(
                "Confronta i documenti del DataFrame filtrato con files/ "
                "e scarica solo quelli mancanti."
            )
            btn_upload.clicked.connect(lambda: self._on_automation_upload(slug))
            btn_row.addWidget(btn_upload)

        btn_del = QPushButton("  Elimina  ")
        btn_del.setStyleSheet(
            "font-size:13px; font-weight:bold; padding:8px 22px;"
            "background:#c62828; color:white; border:none; border-radius:4px;"
        )
        btn_del.setToolTip("Elimina la cartella automazione e chiude questa tab")
        btn_del.clicked.connect(lambda: self._on_automation_delete(slug))
        btn_row.addWidget(btn_del)

        btn_open_plots = QPushButton("  Apri plots  ")
        btn_open_plots.setStyleSheet(
            "font-size:12px; padding:8px 14px;"
            "background:#eceff1; color:#37474f; border:1px solid #b0bec5;"
            " border-radius:4px;"
        )
        btn_open_plots.setToolTip("Apre la cartella files/plots nel file manager")
        btn_open_plots.clicked.connect(lambda: self._on_automation_open_plots(slug))
        btn_row.addWidget(btn_open_plots)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        log_lbl = QLabel("Output (stdout / stderr)")
        log_lbl.setStyleSheet("font-size:12px; color:#424242;")
        lay.addWidget(log_lbl)

        log = QTextEdit()
        log.setReadOnly(True)
        log.setAcceptRichText(True)
        log.setPlaceholderText(
            "print() → nero · stderr → arancio · errori → rosso · ok → verde"
        )
        log.setStyleSheet(
            "QTextEdit { font-family: Consolas, 'Courier New', monospace;"
            " font-size:12px; color:#212121; background:#fafafa;"
            " border:1px solid #bdbdbd; border-radius:4px; padding:6px; }"
        )
        lay.addWidget(log, stretch=2)

        plots_hdr = QHBoxLayout()
        plots_lbl = QLabel("Grafici (files/plots) — doppio click per aprire")
        plots_lbl.setStyleSheet("font-size:12px; color:#424242;")
        plots_hdr.addWidget(plots_lbl)
        plots_hdr.addStretch()
        lay.addLayout(plots_hdr)

        plots_scroll = QScrollArea()
        plots_scroll.setWidgetResizable(True)
        plots_scroll.setMinimumHeight(170)
        plots_scroll.setStyleSheet(
            "QScrollArea { border:1px solid #bdbdbd; border-radius:4px;"
            " background:#eeeeee; }"
        )
        plots_host = QWidget()
        plots_lay = QHBoxLayout(plots_host)
        plots_lay.setContentsMargins(8, 8, 8, 8)
        plots_lay.setSpacing(10)
        plots_empty = QLabel(
            "Nessun grafico. In main.py usa save_plot(fig, files_dir, \"nome\")."
        )
        plots_empty.setStyleSheet("font-size:12px; color:#9e9e9e;")
        plots_lay.addWidget(plots_empty)
        plots_lay.addStretch()
        plots_scroll.setWidget(plots_host)
        lay.addWidget(plots_scroll, stretch=1)

        # Insert before the '+' tab so '+' stays last
        self._sync_add_tab_index()
        idx = self._result_tabs.insertTab(self._add_tab_index, tab, f"  {name}  ")
        self._sync_add_tab_index()
        self._automation_tabs[slug] = {
            **info,
            "widget": tab,
            "log": log,
            "plots_host": plots_host,
            "plots_lay": plots_lay,
            "btn_run": btn_run,
            "btn_upload": btn_upload,
            "btn_del": btn_del,
        }
        self._refresh_automation_plots(slug)
        if select:
            self._last_result_tab = idx
            self._result_tabs.setCurrentIndex(idx)
        if announce:
            self._statusbar.showMessage(
                f"Automazione «{name}» creata → automations/{root.name}/", 6000
            )

    def _automation_info(self, slug: str) -> dict[str, Any] | None:
        return self._automation_tabs.get(slug)

    def _append_automation_log(
        self,
        slug: str,
        text: str,
        *,
        kind: str = "stdout",
    ) -> None:
        meta = self._automation_info(slug)
        if not meta or not text:
            return
        log: QTextEdit = meta["log"]
        colors = {
            "info": "#1565c0",
            "stdout": "#212121",
            "stderr": "#ef6c00",
            "error": "#c62828",
            "ok": "#2e7d32",
        }
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(colors.get(kind, "#212121")))
        if kind in ("error", "info", "ok"):
            fmt.setFontWeight(QFont.Bold)
        cursor = log.textCursor()
        cursor.movePosition(QTextCursor.End)
        # Ensure monospace
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        fmt.setFont(font)
        if not text.endswith("\n"):
            text = text + "\n"
        cursor.insertText(text, fmt)
        log.setTextCursor(cursor)
        log.ensureCursorVisible()

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _refresh_automation_plots(self, slug: str) -> None:
        meta = self._automation_info(slug)
        if not meta:
            return
        layout = meta["plots_lay"]
        self._clear_layout(layout)
        images = list_plot_images(Path(meta["files_dir"]))
        if not images:
            empty = QLabel(
                "Nessun grafico. In main.py usa save_plot(fig, files_dir, \"nome\")."
            )
            empty.setStyleSheet("font-size:12px; color:#9e9e9e;")
            layout.addWidget(empty)
            layout.addStretch()
            return
        for path in images:
            layout.addWidget(ClickablePlotLabel(path))
        layout.addStretch()

    def _on_automation_open_plots(self, slug: str) -> None:
        meta = self._automation_info(slug)
        if not meta:
            return
        plots = Path(meta["files_dir"]) / "plots"
        plots.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(plots.resolve())))

    @Slot()
    def _on_automation_run(self, slug: str) -> None:
        meta = self._automation_info(slug)
        if not meta:
            return
        if self._downloading:
            QMessageBox.information(
                self, "Occupato", "Attendi la fine del download in corso."
            )
            return

        script: Path = meta["script"]
        if not script.is_file():
            QMessageBox.warning(
                self, "Run", f"Script non trovato:\n{script}"
            )
            return

        df = self._filtered_df().copy()
        files_dir = Path(meta["files_dir"])
        files_dir.mkdir(parents=True, exist_ok=True)
        (files_dir / "plots").mkdir(parents=True, exist_ok=True)

        meta["log"].clear()
        self._append_automation_log(
            slug,
            f"=== Run «{meta['name']}» — {len(df)} righe filtrate ===",
            kind="info",
        )
        self._overlay.show_loading(f"Esecuzione automazione «{meta['name']}»…")
        meta["btn_run"].setEnabled(False)
        if meta.get("btn_upload") is not None:
            meta["btn_upload"].setEnabled(False)
        meta["btn_del"].setEnabled(False)

        # Snapshot images before run to highlight new ones
        before = {p: p.stat().st_mtime for p in list_plot_images(files_dir)}

        def _do_run() -> None:
            buf_out = io.StringIO()
            buf_err = io.StringIO()
            err = ""
            src_dir = str(script.parent.resolve())
            path_added = False
            show_patched = False
            original_show = None
            try:
                if src_dir not in sys.path:
                    sys.path.insert(0, src_dir)
                    path_added = True

                # Non-interactive matplotlib + plt.show() → save into files/plots
                try:
                    import matplotlib

                    matplotlib.use("Agg", force=True)
                    import matplotlib.pyplot as plt

                    counter = {"n": 0}

                    def _patched_show(*_a, **_kw):
                        plots = files_dir / "plots"
                        plots.mkdir(parents=True, exist_ok=True)
                        for num in plt.get_fignums():
                            fig = plt.figure(num)
                            counter["n"] += 1
                            out = plots / f"plot_{counter['n']}.png"
                            fig.savefig(out, dpi=120, bbox_inches="tight")
                            print(f"[plot saved via plt.show()] {out}")
                        plt.close("all")

                    original_show = plt.show
                    plt.show = _patched_show  # type: ignore[assignment]
                    show_patched = True
                except ImportError:
                    pass

                mod_name = f"proligent_automation_{slug}"
                to_drop = [
                    k for k in list(sys.modules)
                    if k == mod_name or k.startswith(mod_name + ".")
                ]
                for k, mod in list(sys.modules.items()):
                    mod_file = getattr(mod, "__file__", None)
                    if not mod_file:
                        continue
                    try:
                        if Path(mod_file).resolve().parent == Path(src_dir):
                            to_drop.append(k)
                    except OSError:
                        pass
                for k in set(to_drop):
                    sys.modules.pop(k, None)

                spec = importlib.util.spec_from_file_location(
                    mod_name, script, submodule_search_locations=[src_dir]
                )
                if spec is None or spec.loader is None:
                    raise RuntimeError(f"Impossibile caricare {script}")
                module = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = module
                with redirect_stdout(buf_out), redirect_stderr(buf_err):
                    spec.loader.exec_module(module)
                    run_fn = getattr(module, "run", None)
                    if not callable(run_fn):
                        raise RuntimeError(
                            "Lo script deve definire una funzione run(df, files_dir)."
                        )
                    run_fn(df, files_dir)
            except Exception:
                err = traceback.format_exc()
            finally:
                if show_patched and original_show is not None:
                    try:
                        import matplotlib.pyplot as plt

                        plt.show = original_show
                    except Exception:
                        pass
                if path_added:
                    try:
                        sys.path.remove(src_dir)
                    except ValueError:
                        pass

            after = list_plot_images(files_dir)
            new_images = [
                str(p) for p in after
                if p not in before or p.stat().st_mtime > before.get(p, 0)
            ]
            self._automation_run_done.emit(
                slug,
                buf_out.getvalue(),
                buf_err.getvalue(),
                err,
                new_images,
            )

        threading.Thread(target=_do_run, daemon=True).start()

    @Slot(str, str, str, str, object)
    def _on_automation_run_done(
        self,
        slug: str,
        stdout: str,
        stderr: str,
        err: str,
        new_images: object,
    ) -> None:
        self._overlay.hide_loading()
        meta = self._automation_info(slug)
        if meta:
            meta["btn_run"].setEnabled(True)
            if meta.get("btn_upload") is not None:
                meta["btn_upload"].setEnabled(True)
            meta["btn_del"].setEnabled(True)
        if stdout.strip():
            self._append_automation_log(slug, stdout.rstrip(), kind="stdout")
        if stderr.strip():
            self._append_automation_log(slug, stderr.rstrip(), kind="stderr")
        if err:
            self._append_automation_log(slug, "--- ERROR ---\n" + err.rstrip(), kind="error")
            QMessageBox.warning(
                self,
                "Errore automazione",
                f"L'automazione «{slug}» ha generato un errore.\n"
                "Dettagli nel pannello Output.",
            )
            self._statusbar.showMessage(f"Automazione «{slug}»: errore", 6000)
        else:
            self._append_automation_log(slug, "=== Fine (ok) ===", kind="ok")
            self._statusbar.showMessage(f"Automazione «{slug}»: completata", 5000)

        self._refresh_automation_plots(slug)
        imgs = list(new_images) if isinstance(new_images, (list, tuple)) else []
        if imgs:
            names = ", ".join(Path(p).name for p in imgs)
            self._append_automation_log(
                slug,
                f"Nuovi grafici ({len(imgs)}): {names}",
                kind="info",
            )

    @Slot()
    def _on_automation_upload(self, slug: str) -> None:
        meta = self._automation_info(slug)
        if not meta:
            return
        self._start_automation_document_download(meta, only_missing=True)

    @Slot()
    def _on_automation_delete(self, slug: str) -> None:
        meta = self._automation_info(slug)
        if not meta:
            return
        name = meta["name"]
        root = Path(meta["root"])
        reply = QMessageBox.question(
            self,
            "Elimina automazione",
            f"Eliminare definitivamente l'automazione «{name}»?\n\n"
            f"Verrà rimossa la cartella:\n{root}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            delete_automation(root)
        except (OSError, ValueError) as e:
            QMessageBox.critical(self, "Elimina automazione", str(e))
            return

        widget = meta["widget"]
        idx = self._result_tabs.indexOf(widget)
        if idx >= 0:
            was_current = self._result_tabs.currentIndex() == idx
            self._result_tabs.removeTab(idx)
            if was_current:
                self._result_tabs.setCurrentIndex(0)
                self._last_result_tab = 0
            elif self._last_result_tab > idx:
                self._last_result_tab -= 1
        self._automation_tabs.pop(slug, None)
        self._sync_add_tab_index()
        self._statusbar.showMessage(f"Automazione «{name}» eliminata", 5000)

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
            self._set_query_buttons_enabled(True)
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
        self._set_query_buttons_enabled(False)
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
        try:
            if err and err.startswith("__WH_"):
                self._handle_wh_connect_result(df, err)
                return
            self._apply_query_result(df, err)
        except Exception as e:
            self._statusbar.showMessage(f"Errore: {e}", 10000)
            QMessageBox.warning(self, "Errore", str(e))
        finally:
            self._set_query_buttons_enabled(True)

    def _apply_query_result(self, df: pd.DataFrame | None, err: str) -> None:
        if err:
            self._statusbar.showMessage(f"Errore: {err}", 10000)
            QMessageBox.warning(self, "Errore", err)
            return
        if df is None or df.empty:
            self._statusbar.showMessage("Nessun dato.", 5000)
            QMessageBox.information(self, "Risultato", "Nessun dato trovato.")
            self._refresh_meas_name_filter(pd.DataFrame())
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
            if col_name in ("_download_url", "_unit_view", "Document URL"):
                self._table.setColumnHidden(i, True)
            else:
                w = h.sectionSize(i)
                h.resizeSection(i, max(min(w + 24, 320), 100))

        self._upd_count()
        if self._dashboard is not None:
            self._dashboard.update_data(self._current_df)
        self._refresh_meas_name_filter(df)
        self._statusbar.showMessage(f"Caricati {len(df)} record (piu' recenti prima).", 5000)

    def _find_meas_name_col(self, df: pd.DataFrame | None = None) -> str | None:
        src = df if df is not None else self._current_df
        if src is None or src.empty:
            return None
        for c in src.columns:
            if str(c).lower() == "measurementname":
                return str(c)
        return None

    def _refresh_meas_name_filter(self, df: pd.DataFrame | None = None) -> None:
        """Populate MeasurementName choices from the latest query result."""
        src = df if df is not None else self._current_df
        col = self._find_meas_name_col(src)
        self._cmb_meas_name.blockSignals(True)
        self._cmb_meas_name.clear()
        self._cmb_meas_name.addItem("(tutti)")
        self._meas_names = []
        self._meas_col_idx = None

        if col is None or src is None or src.empty:
            self._cmb_meas_name.setEnabled(False)
            self._btn_meas_multi.setEnabled(False)
            self._btn_meas_clear.setEnabled(False)
            self._lbl_meas_info.setText("Nessun MeasurementName in questo risultato")
            self._cmb_meas_name.blockSignals(False)
            return

        names = sorted(
            {
                str(v)
                for v in src[col].dropna().tolist()
                if str(v).strip() and str(v).lower() != "nan"
            },
            key=str.lower,
        )
        self._meas_names = names
        self._meas_col_idx = list(src.columns).index(col)
        self._cmb_meas_name.addItems(names)
        completer = QCompleter(names, self._cmb_meas_name)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self._cmb_meas_name.setCompleter(completer)
        self._cmb_meas_name.setEnabled(True)
        self._btn_meas_multi.setEnabled(True)
        self._btn_meas_clear.setEnabled(True)
        self._lbl_meas_info.setText(f"{len(names)} MeasurementName dalla query")
        self._cmb_meas_name.setCurrentIndex(0)
        self._cmb_meas_name.blockSignals(False)

    def _apply_meas_name_filter(self, allowed: set[str] | None) -> None:
        if self._meas_col_idx is None:
            return
        self._proxy.set_column_allowed(self._meas_col_idx, allowed)
        self._upd_count()
        self._upd_filt()
        if allowed is None:
            self._statusbar.showMessage("Filtro MeasurementName rimosso", 3000)
        else:
            self._statusbar.showMessage(
                f"Filtro MeasurementName: {len(allowed)} selezionati", 4000
            )

    @Slot(str)
    def _on_meas_name_combo(self, text: str) -> None:
        if not self._cmb_meas_name.isEnabled():
            return
        text = (text or "").strip()
        if not text or text == "(tutti)":
            self._apply_meas_name_filter(None)
            return
        # Only apply when the typed/selected value exists in the query catalog.
        if text in self._meas_names:
            self._apply_meas_name_filter({text})

    @Slot()
    def _on_meas_name_multi(self) -> None:
        if not self._meas_names or self._meas_col_idx is None:
            return
        active = self._proxy.get_active_filters().get(self._meas_col_idx)
        dlg = FilterDialog("MeasurementName", self._meas_names, active, self)
        if dlg.exec() == QDialog.Accepted:
            vals = dlg.result_values
            if vals is None or len(vals) >= len(self._meas_names):
                self._cmb_meas_name.blockSignals(True)
                self._cmb_meas_name.setCurrentIndex(0)
                self._cmb_meas_name.blockSignals(False)
                self._apply_meas_name_filter(None)
            elif len(vals) == 1:
                only = next(iter(vals))
                self._cmb_meas_name.blockSignals(True)
                idx = self._cmb_meas_name.findText(only)
                if idx >= 0:
                    self._cmb_meas_name.setCurrentIndex(idx)
                else:
                    self._cmb_meas_name.setCurrentText(only)
                self._cmb_meas_name.blockSignals(False)
                self._apply_meas_name_filter(vals)
            else:
                self._cmb_meas_name.blockSignals(True)
                self._cmb_meas_name.setCurrentText(f"({len(vals)} selezionati)")
                self._cmb_meas_name.blockSignals(False)
                self._apply_meas_name_filter(vals)

    @Slot()
    def _clear_meas_name_filter(self) -> None:
        self._cmb_meas_name.blockSignals(True)
        self._cmb_meas_name.setCurrentIndex(0)
        self._cmb_meas_name.blockSignals(False)
        self._apply_meas_name_filter(None)

    # ── Warehouse DB ──

    @Slot(bool)
    def _on_wh_dates_toggled(self, checked: bool) -> None:
        self._date_wh_from.setEnabled(checked)
        self._date_wh_to.setEnabled(checked)

    @Slot()
    def _on_wh_connect(self) -> None:
        self._set_query_buttons_enabled(False)
        self._lbl_wh_status.setText("  Warehouse: connessione…")
        self._lbl_wh_status.setStyleSheet("font-size:12px; color:#757575;")
        self._overlay.show_loading("Connessione al warehouse SQL…")
        threading.Thread(target=self._do_wh_connect, daemon=True).start()

    def _do_wh_connect(self) -> None:
        try:
            self._get_wh_client().connect()
            self._query_done.emit(pd.DataFrame(), "__WH_OK__")
        except Exception as e:
            self._query_done.emit(None, f"__WH_ERR__{e}")

    @Slot()
    def _on_wh_query(self) -> None:
        if not self._wh_connected:
            return
        product = self._txt_wh_product.text().strip()
        serial = self._txt_wh_serial.text().strip()
        operation = self._txt_wh_operation.text().strip()
        station = self._txt_wh_station.text().strip()
        operator = self._txt_wh_operator.text().strip()
        measurement = self._txt_wh_measurement.text().strip()
        if not any((product, serial, operation, station, operator, measurement)):
            QMessageBox.warning(
                self,
                "Filtri richiesti",
                "Imposta almeno un filtro (prodotto, serial, operazione, "
                "stazione, operatore o MeasurementName) per evitare estrazioni enormi.",
            )
            return

        self._set_query_buttons_enabled(False)
        self._statusbar.showMessage("Warehouse query in corso...")
        self._overlay.show_loading("Query warehouse SQL…")
        threading.Thread(target=self._do_wh_query, daemon=True).start()

    def _do_wh_query(self) -> None:
        try:
            wh = self._get_wh_client()
            qtype = self._cmb_wh_type.currentText()
            if self._chk_wh_dates.isChecked():
                date_from = self._date_wh_from.date().toString("yyyy-MM-dd")
                date_to = self._date_wh_to.date().toString("yyyy-MM-dd")
            else:
                date_from = None
                date_to = None
            common = dict(
                product=self._txt_wh_product.text().strip() or None,
                serial=self._txt_wh_serial.text().strip() or None,
                operation=self._txt_wh_operation.text().strip() or None,
                station=self._txt_wh_station.text().strip() or None,
                date_from=date_from,
                date_to=date_to,
            )
            self._progress_msg.emit("Esecuzione query SQL sul warehouse…")
            if qtype.startswith("Measurements"):
                df = wh.fetch_measurements(
                    **common,
                    measurement_name=self._txt_wh_measurement.text().strip() or None,
                )
            else:
                st = self._cmb_wh_status.currentText().strip()
                top = self._spn_wh_top.value()
                df = wh.fetch_operation_runs(
                    **common,
                    operator=self._txt_wh_operator.text().strip() or None,
                    status=None if st == "(tutti)" else st,
                    top=top if top > 0 else None,
                    product_like=self._chk_wh_product_like.isChecked(),
                    latest_passage_only=self._chk_wh_latest.isChecked(),
                )
            self._query_done.emit(df, "")
        except Exception as e:
            self._query_done.emit(None, str(e))

    def _handle_wh_connect_result(self, df: pd.DataFrame | None, err: str) -> bool:
        """Handle warehouse connect sentinel results. Returns True if consumed."""
        if err == "__WH_OK__":
            self._wh_connected = True
            self._lbl_wh_status.setText("  Warehouse: connesso")
            self._lbl_wh_status.setStyleSheet(
                "font-size:12px; color:#2e7d32; font-weight:bold;"
            )
            self._statusbar.showMessage("Warehouse connesso.", 4000)
            return True
        if err.startswith("__WH_ERR__"):
            self._wh_connected = False
            msg = err[len("__WH_ERR__"):]
            self._lbl_wh_status.setText("  Warehouse: errore")
            self._lbl_wh_status.setStyleSheet("font-size:12px; color:red;")
            QMessageBox.critical(self, "Warehouse", msg)
            return True
        return False

    # ── Warehouse query persistence ──

    def _wh_query_snapshot(self) -> dict:
        """Capture current warehouse form fields."""
        label = self._txt_wh_label.text().strip()
        if not label:
            parts = [
                self._txt_wh_product.text().strip(),
                self._txt_wh_station.text().strip(),
                self._txt_wh_operator.text().strip(),
                self._txt_wh_serial.text().strip(),
                self._txt_wh_operation.text().strip(),
                self._txt_wh_measurement.text().strip(),
            ]
            label = " / ".join(p for p in parts if p) or self._cmb_wh_type.currentText()
        return {
            "label": label,
            "query_type": self._cmb_wh_type.currentText(),
            "product": self._txt_wh_product.text().strip(),
            "serial": self._txt_wh_serial.text().strip(),
            "operation": self._txt_wh_operation.text().strip(),
            "station": self._txt_wh_station.text().strip(),
            "operator": self._txt_wh_operator.text().strip(),
            "measurement_name": self._txt_wh_measurement.text().strip(),
            "status": self._cmb_wh_status.currentText(),
            "top": self._spn_wh_top.value(),
            "filter_dates": self._chk_wh_dates.isChecked(),
            "date_from": self._date_wh_from.date().toString("yyyy-MM-dd"),
            "date_to": self._date_wh_to.date().toString("yyyy-MM-dd"),
            "latest_passage_only": self._chk_wh_latest.isChecked(),
            "product_like": self._chk_wh_product_like.isChecked(),
        }

    def _wh_query_summary(self, q: dict) -> str:
        bits = [q.get("query_type", "")]
        for key in (
            "product", "serial", "operation", "station", "operator",
            "measurement_name", "status",
        ):
            val = (q.get(key) or "").strip()
            if val and val != "(tutti)":
                bits.append(val)
        if q.get("filter_dates"):
            bits.append(f"{q.get('date_from', '')}→{q.get('date_to', '')}")
        return " | ".join(b for b in bits if b)

    def _apply_wh_query(self, q: dict) -> None:
        """Restore warehouse form from a saved search."""
        qtype = q.get("query_type", "Operation runs (+ docs)")
        idx = self._cmb_wh_type.findText(qtype)
        self._cmb_wh_type.setCurrentIndex(idx if idx >= 0 else 0)
        self._txt_wh_product.setText(q.get("product", ""))
        self._txt_wh_serial.setText(q.get("serial", ""))
        self._txt_wh_operation.setText(q.get("operation", ""))
        self._txt_wh_station.setText(q.get("station", ""))
        self._txt_wh_operator.setText(q.get("operator", ""))
        self._txt_wh_measurement.setText(q.get("measurement_name", ""))
        status = q.get("status", "(tutti)")
        sidx = self._cmb_wh_status.findText(status)
        self._cmb_wh_status.setCurrentIndex(sidx if sidx >= 0 else 0)
        self._spn_wh_top.setValue(int(q.get("top", 10_000) or 0))
        self._chk_wh_dates.setChecked(bool(q.get("filter_dates", False)))
        d_from = q.get("date_from") or ""
        d_to = q.get("date_to") or ""
        if d_from:
            self._date_wh_from.setDate(QDate.fromString(d_from, "yyyy-MM-dd"))
        if d_to:
            self._date_wh_to.setDate(QDate.fromString(d_to, "yyyy-MM-dd"))
        self._chk_wh_latest.setChecked(bool(q.get("latest_passage_only", False)))
        self._chk_wh_product_like.setChecked(bool(q.get("product_like", True)))
        self._txt_wh_label.setText(q.get("label", ""))

    def _load_saved_warehouse_queries(self) -> None:
        self._saved_wh_queries: list[dict] = []
        if _SAVED_WAREHOUSE_FILE.exists():
            try:
                data = json.loads(_SAVED_WAREHOUSE_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._saved_wh_queries = data
            except (json.JSONDecodeError, OSError):
                self._saved_wh_queries = []
        self._refresh_wh_saved_combo()

    def _persist_warehouse_queries(self) -> None:
        _SAVED_WAREHOUSE_FILE.write_text(
            json.dumps(self._saved_wh_queries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _refresh_wh_saved_combo(self) -> None:
        self._cmb_wh_saved.blockSignals(True)
        current = self._cmb_wh_saved.currentIndex()
        self._cmb_wh_saved.clear()
        self._cmb_wh_saved.addItem("(nuova ricerca)", -1)
        for i, q in enumerate(self._saved_wh_queries):
            label = q.get("label") or self._wh_query_summary(q)
            self._cmb_wh_saved.addItem(f"{label}  —  {self._wh_query_summary(q)}", i)
        if 0 <= current < self._cmb_wh_saved.count():
            self._cmb_wh_saved.setCurrentIndex(current)
        else:
            self._cmb_wh_saved.setCurrentIndex(0)
        self._cmb_wh_saved.blockSignals(False)

    @Slot(int)
    def _on_wh_saved_selected(self, index: int) -> None:
        if index <= 0:
            return
        data = self._cmb_wh_saved.itemData(index)
        if data is None or int(data) < 0:
            return
        idx = int(data)
        if 0 <= idx < len(self._saved_wh_queries):
            self._apply_wh_query(self._saved_wh_queries[idx])
            self._statusbar.showMessage(
                f"Ricerca caricata: {self._saved_wh_queries[idx].get('label', '')}",
                3000,
            )

    @Slot()
    def _on_save_warehouse_query(self) -> None:
        snap = self._wh_query_snapshot()
        if not any(
            snap.get(k)
            for k in (
                "product", "serial", "operation", "station",
                "operator", "measurement_name",
            )
        ):
            QMessageBox.warning(
                self,
                "Salva ricerca",
                "Imposta almeno un filtro (prodotto, serial, operazione, "
                "stazione, operatore o MeasurementName) prima di salvare.",
            )
            return

        label = snap["label"]
        for q in self._saved_wh_queries:
            if q.get("label") == label:
                q.clear()
                q.update(snap)
                self._persist_warehouse_queries()
                self._refresh_wh_saved_combo()
                # Select the updated entry
                for i in range(self._cmb_wh_saved.count()):
                    if self._cmb_wh_saved.itemData(i) is not None and int(
                        self._cmb_wh_saved.itemData(i)
                    ) >= 0:
                        qi = self._saved_wh_queries[int(self._cmb_wh_saved.itemData(i))]
                        if qi.get("label") == label:
                            self._cmb_wh_saved.setCurrentIndex(i)
                            break
                self._statusbar.showMessage(f"Ricerca aggiornata: {label}", 3000)
                return

        self._saved_wh_queries.append(snap)
        self._persist_warehouse_queries()
        self._refresh_wh_saved_combo()
        self._cmb_wh_saved.setCurrentIndex(self._cmb_wh_saved.count() - 1)
        self._statusbar.showMessage(f"Ricerca salvata: {label}", 3000)

    @Slot()
    def _on_del_warehouse_query(self) -> None:
        index = self._cmb_wh_saved.currentIndex()
        data = self._cmb_wh_saved.itemData(index) if index >= 0 else None
        if data is None or int(data) < 0:
            QMessageBox.warning(
                self,
                "Elimina ricerca",
                "Seleziona una ricerca salvata da eliminare.",
            )
            return
        idx = int(data)
        q = self._saved_wh_queries[idx]
        name = q.get("label") or self._wh_query_summary(q)
        reply = QMessageBox.question(
            self,
            "Conferma eliminazione",
            f"Eliminare la ricerca \"{name}\"?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._saved_wh_queries.pop(idx)
            self._persist_warehouse_queries()
            self._refresh_wh_saved_combo()
            self._cmb_wh_saved.setCurrentIndex(0)
            self._statusbar.showMessage(f"Ricerca eliminata: {name}", 3000)

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
        self._refresh_meas_name_filter(filtered)
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
        self._refresh_meas_name_filter(self._current_df)
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
        self._sync_add_tab_index()
        if index == self._add_tab_index:
            # Don't stay on '+': restore previous tab, then open the dialog
            self._result_tabs.blockSignals(True)
            self._result_tabs.setCurrentIndex(self._last_result_tab)
            self._result_tabs.blockSignals(False)
            self._on_add_automation()
            return

        self._last_result_tab = index
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
        if self._cmb_meas_name.isEnabled():
            self._cmb_meas_name.blockSignals(True)
            self._cmb_meas_name.setCurrentIndex(0)
            self._cmb_meas_name.blockSignals(False)
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

        from warehouse_client import download_url_to_file, is_direct_document_url

        serial = ""
        file_hint = ""
        df = self._model.dataframe
        if not df.empty and 0 <= row < len(df):
            for c in df.columns:
                cl = str(c).lower()
                val = df.iat[row, df.columns.get_loc(c)]
                if pd.isna(val):
                    continue
                text = str(val)
                if not serial and "serial" in cl:
                    serial = text
                if not file_hint and cl in ("file name", "filename"):
                    file_hint = text

        if file_hint:
            filename_hint = file_hint
        elif serial:
            filename_hint = f"documents_{serial}"
        else:
            filename_hint = "document"

        # Warehouse reports are often .html / compressed blobs, not zip.
        if is_direct_document_url(url) and "." not in filename_hint:
            filename_hint += ".bin"
        elif not is_direct_document_url(url) and not filename_hint.lower().endswith(".zip"):
            filename_hint += ".zip"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salva documenti",
            filename_hint,
            "Tutti (*);;ZIP (*.zip);;HTML (*.html)",
        )
        if not save_path:
            return

        self._downloading = True
        self._overlay.show_loading(f"Download documenti {serial or ''}…")

        needs_web = not is_direct_document_url(url)

        def _do_download():
            try:
                session = None
                if needs_web:
                    if not self._logged_in:
                        raise RuntimeError(
                            "Login Proligent richiesto per scaricare "
                            "documenti da Shortcut / report web."
                        )
                    session = self._get_client().session
                download_url_to_file(url, save_path, session=session)
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
        if self._wh_client is not None:
            try:
                self._wh_client.close()
            except Exception:
                pass
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
