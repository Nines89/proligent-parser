"""Dashboard tab with KPI cards and charts (lazy-loaded from gui.py)."""

from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

FONT_FAMILY = "Segoe UI"

_STATUS_COLORS = {
    "PASS": "#66bb6a",
    "FAIL": "#ef5350",
    "ABORTED": "#ffca28",
}


def _find_col(df: pd.DataFrame, *, exact: str | None = None,
              contains: tuple[str, ...] = ()) -> str | None:
    if exact:
        for c in df.columns:
            if str(c).strip().lower() == exact:
                return str(c)
    for key in contains:
        for c in df.columns:
            if key in str(c).lower():
                return str(c)
    return None


def _to_seconds(series: pd.Series) -> pd.Series:
    """Parse duration strings like ``HH:MM:SS.mmm`` into total seconds."""
    td = pd.to_timedelta(series.astype(str).str.strip(), errors="coerce")
    return td.dt.total_seconds()


def _short_label(name: Any, limit: int = 16) -> str:
    """Shorten a product label to just the mnemonic, truncated if long."""
    s = str(name)
    if " -> " in s:
        s = s.split(" -> ")[0]
    return s if len(s) <= limit else s[: limit - 1] + "\u2026"


def _unique_labels(labels: list[str]) -> list[str]:
    """Ensure category labels are unique (bar axes require it)."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for lbl in labels:
        if lbl in seen:
            seen[lbl] += 1
            out.append(f"{lbl} ({seen[lbl]})")
        else:
            seen[lbl] = 0
            out.append(lbl)
    return out


class KpiCard(QFrame):
    """A small card showing a big value and a caption."""

    def __init__(self, title: str, color: str = "#1565c0") -> None:
        super().__init__()
        self.setStyleSheet(
            "QFrame { background:white; border:1px solid #e0e0e0;"
            f" border-radius:8px; border-left:5px solid {color}; }}"
        )
        self.setMinimumWidth(150)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(2)
        self._value = QLabel("\u2014")
        self._value.setStyleSheet(
            f"font-size:26px; font-weight:bold; color:{color}; border:none;"
        )
        cap = QLabel(title)
        cap.setStyleSheet("font-size:12px; color:#757575; border:none;")
        lay.addWidget(self._value)
        lay.addWidget(cap)

    def set_value(self, value: Any) -> None:
        self._value.setText(str(value))


class DashboardWidget(QWidget):
    """Summary dashboard: KPI cards + charts, driven by a DataFrame."""

    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet("background:#eef1f5;")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        self._v = QVBoxLayout(content)
        self._v.setContentsMargins(16, 16, 16, 16)
        self._v.setSpacing(16)

        self._empty = QLabel("Carica dei dati per popolare la dashboard.")
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet("font-size:15px; color:#9e9e9e; padding:60px;")
        self._v.addWidget(self._empty)

        self._cards: dict[str, KpiCard] = {}
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        for key, title, color in [
            ("records", "Record totali", "#1565c0"),
            ("serials", "Serial number", "#00838f"),
            ("products", "Prodotti", "#6a1b9a"),
            ("yield", "Yield (Pass)", "#2e7d32"),
            ("fail", "Fail", "#c62828"),
        ]:
            card = KpiCard(title, color)
            self._cards[key] = card
            kpi_row.addWidget(card)
        self._kpi_container = QWidget()
        self._kpi_container.setLayout(kpi_row)
        self._v.addWidget(self._kpi_container)

        grid = QGridLayout()
        grid.setSpacing(16)
        self._chart_status = self._make_chart_view()
        self._chart_products = self._make_chart_view()
        self._chart_yield = self._make_chart_view()
        self._chart_avgtime = self._make_chart_view()
        self._chart_time = self._make_chart_view()
        grid.addWidget(self._chart_status, 0, 0)
        grid.addWidget(self._chart_products, 0, 1)
        grid.addWidget(self._chart_yield, 1, 0)
        grid.addWidget(self._chart_avgtime, 1, 1)
        grid.addWidget(self._chart_time, 2, 0, 1, 2)
        self._charts_container = QWidget()
        self._charts_container.setLayout(grid)
        self._v.addWidget(self._charts_container)
        self._v.addStretch()

        self._show_empty(True)

    @staticmethod
    def _make_chart_view() -> QChartView:
        view = QChartView()
        view.setRenderHint(QPainter.Antialiasing)
        view.setMinimumHeight(300)
        view.setStyleSheet(
            "background:white; border:1px solid #e0e0e0; border-radius:8px;"
        )
        return view

    @staticmethod
    def _style_chart(chart: QChart, title: str) -> None:
        chart.setTitle(title)
        chart.setTitleBrush(QColor("#37474f"))
        chart.setTitleFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        chart.setBackgroundBrush(QColor("white"))
        chart.setBackgroundRoundness(8)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setMargins(QMargins(6, 6, 6, 6))

    def _show_empty(self, empty: bool) -> None:
        self._empty.setVisible(empty)
        self._kpi_container.setVisible(not empty)
        self._charts_container.setVisible(not empty)

    def update_data(self, df: pd.DataFrame | None) -> None:
        if df is None or df.empty:
            self._show_empty(True)
            return
        self._show_empty(False)

        status_col = _find_col(df, exact="status", contains=("status",))
        serial_col = _find_col(df, contains=("serial",))
        product_col = _find_col(df, exact="product", contains=("product",))
        time_col = _find_col(df, contains=("start time", "time", "date"))
        dur_col = _find_col(df, contains=("cycle time", "cycle", "duration"))

        self._cards["records"].set_value(f"{len(df):,}".replace(",", "."))
        self._cards["serials"].set_value(
            df[serial_col].nunique() if serial_col else "\u2014"
        )
        self._cards["products"].set_value(
            df[product_col].nunique() if product_col else "\u2014"
        )

        counts: dict[str, int] = {}
        if status_col:
            s = df[status_col].fillna("").astype(str).str.strip().str.upper()
            counts = {k: int(v) for k, v in s.value_counts().items() if k}
        tested = counts.get("PASS", 0) + counts.get("FAIL", 0)
        yield_pct = (counts.get("PASS", 0) / tested * 100) if tested else 0.0
        self._cards["yield"].set_value(
            f"{yield_pct:.1f}%" if status_col else "\u2014"
        )
        self._cards["fail"].set_value(
            counts.get("FAIL", 0) if status_col else "\u2014"
        )

        self._build_status_chart(counts)
        self._build_products_chart(df, product_col)
        self._build_yield_chart(df, product_col, status_col)
        self._build_avgtime_chart(df, product_col, dur_col)
        self._build_time_chart(df, time_col)

    def _build_status_chart(self, counts: dict[str, int]) -> None:
        chart = QChart()
        self._style_chart(chart, "Distribuzione esiti")
        if counts:
            series = QPieSeries()
            series.setHoleSize(0.45)
            # External callouts + leader lines overlap badly when slices
            # are uneven; legend carries name / count / percentage instead.
            series.setLabelsVisible(False)
            total = sum(counts.values()) or 1
            order = ["PASS", "FAIL", "ABORTED"]
            keys = [k for k in order if k in counts]
            keys += [k for k in counts if k not in order]
            for k in keys:
                n = counts[k]
                pct = n / total * 100
                sl = series.append(f"{k.title()}  {n}  ({pct:.1f}%)", n)
                sl.setBrush(QColor(_STATUS_COLORS.get(k, "#90a4ae")))
                sl.setLabelVisible(False)
            chart.addSeries(series)
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)
            chart.legend().setLabelColor(QColor("#37474f"))
            chart.legend().setFont(QFont(FONT_FAMILY, 9))
        else:
            chart.legend().setVisible(False)
        self._chart_status.setChart(chart)

    def _build_bar_chart(self, view: QChartView, title: str,
                         labels: list[str], values: list[float],
                         color: str, y_max: float | None = None) -> None:
        chart = QChart()
        self._style_chart(chart, title)
        chart.legend().setVisible(False)
        if labels:
            bar = QBarSet("")
            bar.setColor(QColor(color))
            bar.setBorderColor(QColor(color))
            for v in values:
                bar.append(v)
            series = QBarSeries()
            series.append(bar)
            series.setLabelsVisible(True)
            series.setLabelsPosition(QBarSeries.LabelsOutsideEnd)
            chart.addSeries(series)
            axis_x = QBarCategoryAxis()
            axis_x.append(_unique_labels(labels))
            axis_x.setLabelsAngle(-45)
            axis_x.setLabelsFont(QFont(FONT_FAMILY, 8))
            axis_x.setLabelsColor(QColor("#546e7a"))
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)
            axis_y = QValueAxis()
            axis_y.setLabelsColor(QColor("#546e7a"))
            if y_max is not None:
                axis_y.setRange(0, y_max)
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)
        view.setChart(chart)

    def _build_products_chart(self, df: pd.DataFrame,
                              product_col: str | None) -> None:
        if not product_col:
            self._build_bar_chart(self._chart_products, "Test per prodotto",
                                   [], [], "#1565c0")
            return
        vc = df[product_col].fillna("\u2014").astype(str).value_counts().head(12)
        labels = [_short_label(x) for x in vc.index]
        self._build_bar_chart(
            self._chart_products, "Test per prodotto",
            labels, [int(v) for v in vc.values], "#1565c0",
        )

    def _build_yield_chart(self, df: pd.DataFrame, product_col: str | None,
                           status_col: str | None) -> None:
        if not product_col or not status_col:
            self._build_bar_chart(self._chart_yield, "Yield per prodotto (%)",
                                   [], [], "#2e7d32", y_max=100)
            return
        st = df[status_col].fillna("").astype(str).str.strip().str.upper()
        tmp = df.assign(_st=st)
        volume = tmp.groupby(product_col).size().sort_values(ascending=False).head(12)
        labels: list[str] = []
        vals: list[float] = []
        for prod in volume.index:
            sub = tmp[tmp[product_col] == prod]["_st"]
            tested = int(sub.isin(["PASS", "FAIL"]).sum())
            passed = int((sub == "PASS").sum())
            labels.append(_short_label(prod))
            vals.append(round(passed / tested * 100, 1) if tested else 0.0)
        self._build_bar_chart(
            self._chart_yield, "Yield per prodotto (%)",
            labels, vals, "#2e7d32", y_max=100,
        )

    def _build_avgtime_chart(self, df: pd.DataFrame, product_col: str | None,
                             dur_col: str | None) -> None:
        base_title = "Tempo medio di test per prodotto"
        if not product_col or not dur_col:
            self._build_bar_chart(self._chart_avgtime, base_title, [], [], "#ef6c00")
            return
        tmp = df.assign(_sec=_to_seconds(df[dur_col])).dropna(subset=["_sec"])
        if tmp.empty:
            self._build_bar_chart(self._chart_avgtime, base_title, [], [], "#ef6c00")
            return
        volume = tmp.groupby(product_col).size().sort_values(ascending=False).head(12)
        avgs = {p: tmp.loc[tmp[product_col] == p, "_sec"].mean() for p in volume.index}

        max_avg = max(avgs.values()) if avgs else 0
        if max_avg >= 3600:
            unit, div = "h", 3600.0
        elif max_avg >= 60:
            unit, div = "min", 60.0
        else:
            unit, div = "s", 1.0

        labels = [_short_label(p) for p in volume.index]
        vals = [round(avgs[p] / div, 1) for p in volume.index]
        self._build_bar_chart(
            self._chart_avgtime, f"{base_title} ({unit})", labels, vals, "#ef6c00",
        )

    def _build_time_chart(self, df: pd.DataFrame, time_col: str | None) -> None:
        if not time_col:
            self._build_bar_chart(self._chart_time, "Test nel tempo",
                                   [], [], "#00838f")
            return
        ts = pd.to_datetime(df[time_col], errors="coerce", utc=True).dt.date.dropna()
        vc = ts.value_counts().sort_index().tail(30)
        labels = [d.strftime("%d/%m") for d in vc.index]
        self._build_bar_chart(
            self._chart_time, "Test nel tempo (per giorno)",
            labels, [int(v) for v in vc.values], "#00838f",
        )
