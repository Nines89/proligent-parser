"""Warehouse access via proligent_db_sdk (SQL Server PROLIGENT_DW).

Used for bulk extracts (thousands of rows) that are too slow through the
SSRS / web API path. Requires:
  - ``pip install -e`` of the local ``proligent_db_sdk`` package
  - SQL Server ODBC driver
  - Network reachability to the warehouse host
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

# Sibling clone used during local development (see requirements.txt).
_DEFAULT_SDK_HINT = (
    r'pip install -e "..\proligent_db_sdk-master"'
)


class WarehouseError(RuntimeError):
    """Raised when the SDK is missing or a warehouse call fails."""


def sdk_available() -> bool:
    try:
        import proligent_db_sdk  # noqa: F401
        return True
    except ImportError:
        return False


def _parse_dt(value: str | datetime | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return pd.to_datetime(text, errors="coerce").to_pydatetime()


def normalize_warehouse_df(df: pd.DataFrame) -> pd.DataFrame:
    """Align SDK column names with the existing GUI / dashboard expectations."""
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df.copy()

    out = df.copy()
    renames: dict[str, str] = {}
    if "operation_status" in out.columns and "Status" not in out.columns:
        renames["operation_status"] = "Status"
    if "serial_number" in out.columns and "Serial Number" not in out.columns:
        renames["serial_number"] = "Serial Number"
    if renames:
        out = out.rename(columns=renames)

    if "Document URL" in out.columns:
        urls = out["Document URL"].fillna("").astype(str)
        out["_download_url"] = urls
        if "Documents" not in out.columns:
            if "Name" in out.columns:
                docs = out["Name"].fillna("").astype(str)
                out["Documents"] = docs.where(urls != "", "")
                out.loc[(out["Documents"] == "") & (urls != ""), "Documents"] = "Download"
            else:
                out["Documents"] = urls.apply(lambda u: "Download" if u else "")
        # Keep Documents visible near the left (after Status when present).
        cols = list(out.columns)
        if "Documents" in cols:
            cols.remove("Documents")
            insert_at = cols.index("Status") + 1 if "Status" in cols else min(3, len(cols))
            cols.insert(insert_at, "Documents")
            out = out[cols]

    return out


def is_direct_document_url(url: str) -> bool:
    """True for warehouse DocumentIntegrationService links (no web session needed)."""
    u = (url or "").lower()
    return (
        "documentintegrationservice" in u
        or "documentprovider.svc" in u
        or "/getdocument" in u
    )


def download_url_to_file(
    url: str,
    save_path: str,
    *,
    session: Any | None = None,
    timeout: int = 120,
) -> None:
    """Download a document URL to ``save_path``.

    Warehouse ``DocumentIntegrationService`` URLs are fetched directly (no
    Proligent web login). SSRS ``/api/documents`` URLs require an authenticated
    ``requests.Session``.
    """
    if not url or not str(url).strip():
        raise WarehouseError("Empty document URL")

    url = str(url).strip()

    if is_direct_document_url(url):
        import urllib.request

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Proligent-Parser/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                with open(save_path, "wb") as f:
                    while True:
                        chunk = resp.read(256 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
        except Exception as exc:
            raise WarehouseError(str(exc) or type(exc).__name__) from exc
        return

    if session is None:
        raise WarehouseError(
            "Proligent web login is required to download this document."
        )

    resp = session.get(url, timeout=timeout, stream=True)
    resp.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in resp.iter_content(256 * 1024):
            if chunk:
                f.write(chunk)


class WarehouseClient:
    """Lazy wrapper around ``proligent_db_sdk.viaSQL``."""

    def __init__(self) -> None:
        self._db: Any = None

    @property
    def connected(self) -> bool:
        return self._db is not None

    def connect(
        self,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        try:
            from proligent_db_sdk import viaSQL
        except ImportError as exc:
            raise WarehouseError(
                "proligent_db_sdk is not installed. "
                f"Install it with: {_DEFAULT_SDK_HINT}"
            ) from exc

        self.close()
        try:
            # verbose=0 avoids ANSI console spam in the GUI log.
            self._db = viaSQL(username=username or None, password=password or None, verbose=0)
        except Exception as exc:
            self._db = None
            raise WarehouseError(str(exc) or type(exc).__name__) from exc

    def close(self) -> None:
        if self._db is not None:
            try:
                self._db.close()
            except Exception:
                pass
            self._db = None

    def _ensure(self) -> None:
        if self._db is None:
            self.connect()

    def fetch_operation_runs(
        self,
        *,
        product: str | None = None,
        serial: str | None = None,
        operation: str | None = None,
        station: str | None = None,
        operator: str | None = None,
        date_from: str | datetime | None = None,
        date_to: str | datetime | None = None,
        status: str | None = None,
        top: int | None = None,
        product_like: bool = True,
        serial_like: bool = False,
        station_like: bool = True,
        operator_like: bool = True,
        latest_passage_only: bool = False,
        doc_name: str | None = None,
    ) -> pd.DataFrame:
        """Bulk operation-run listing with document links (warehouse view).

        Includes an ``operator`` filter (SQL on ``[Operator]``) that the SDK
        does not expose natively.
        """
        self._ensure()
        assert self._db is not None

        start = _parse_dt(date_from)
        end = _parse_dt(date_to)
        # Inclusive end-of-day when only a date was provided.
        if end is not None and end.hour == 0 and end.minute == 0 and end.second == 0:
            end = end.replace(hour=23, minute=59, second=59)

        ops = operation.strip() if operation and operation.strip() else None
        st = status.strip() if status and status.strip() else None
        if st and st.lower() in ("(tutti)", "all", "*"):
            st = None
        op_user = operator.strip() if operator and operator.strip() else None

        try:
            df = self._fetch_operation_runs_sql(
                product=product or None,
                serial=serial or None,
                operation=ops,
                station=station or None,
                operator=op_user,
                start=start,
                end=end,
                status=st,
                top=top if top and top > 0 else None,
                product_like=bool(product) and product_like,
                serial_like=bool(serial) and serial_like,
                station_like=bool(station) and station_like,
                operator_like=operator_like,
                latest_passage_only=latest_passage_only,
                doc_name=doc_name or None,
            )
        except Exception as exc:
            raise WarehouseError(str(exc) or type(exc).__name__) from exc

        return normalize_warehouse_df(df)

    def _fetch_operation_runs_sql(
        self,
        *,
        product: str | None,
        serial: str | None,
        operation: str | None,
        station: str | None,
        operator: str | None,
        start: datetime | None,
        end: datetime | None,
        status: str | None,
        top: int | None,
        product_like: bool,
        serial_like: bool,
        station_like: bool,
        operator_like: bool,
        latest_passage_only: bool,
        doc_name: str | None,
    ) -> pd.DataFrame:
        """Query the same warehouse view as the SDK, with Operator support."""
        assert self._db is not None

        def _escape_like(val: str) -> str:
            return val.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        columns = (
            "[Serial Number]",
            "[Product]",
            "[Operation]",
            "[Status]",
            "[Start Time]",
            "[End Time]",
            "[Location + Station]",
            "[Operation Passage Order]",
            "[Operator]",
            "[Process Mode]",
            "[Top Process]",
            "[Name]",
            "[File Name]",
            "[Document URL]",
        )
        select_list = ", ".join(columns)
        from_clause = " FROM [PROLIGENT_DW].[NOKIA].[V_NOKIA_OperationRunListing_W_DocLink]"

        params: list[Any] = []
        if top is not None:
            base_sql = "SELECT TOP (?) " + select_list + from_clause
            params.append(top)
        else:
            base_sql = "SELECT " + select_list + from_clause

        conditions: list[str] = []
        if product:
            if product_like:
                conditions.append("[Product] LIKE ? ESCAPE '\\'")
                params.append(_escape_like(product) + "%")
            else:
                conditions.append("[Product] = ?")
                params.append(product)
        if serial:
            if serial_like:
                conditions.append("[Serial Number] LIKE ? ESCAPE '\\'")
                params.append(_escape_like(serial) + "%")
            else:
                conditions.append("[Serial Number] = ?")
                params.append(serial)
        if operation:
            conditions.append("[Operation] = ?")
            params.append(operation)
        if station:
            if station_like:
                conditions.append("[Location + Station] LIKE ? ESCAPE '\\'")
                params.append("%" + _escape_like(station) + "%")
            else:
                conditions.append("[Location + Station] = ?")
                params.append(station)
        if operator:
            if operator_like:
                conditions.append("[Operator] LIKE ? ESCAPE '\\'")
                params.append("%" + _escape_like(operator) + "%")
            else:
                conditions.append("[Operator] = ?")
                params.append(operator)
        if doc_name:
            conditions.append("[Name] = ?")
            params.append(doc_name)
        if status:
            conditions.append("[Status] = ?")
            params.append(status)
        if start is not None:
            conditions.append("[End Time] >= ?")
            params.append(start.strftime("%Y-%m-%d %H:%M:%S"))
        if end is not None:
            conditions.append("[End Time] <= ?")
            params.append(end.strftime("%Y-%m-%d %H:%M:%S"))

        if latest_passage_only:
            inner = (
                "SELECT " + select_list
                + ", ROW_NUMBER() OVER (PARTITION BY [Serial Number] "
                "ORDER BY [Operation Passage Order] DESC) AS _rn"
                + from_clause
            )
            if conditions:
                inner += " WHERE " + " AND ".join(conditions)
            if top is not None:
                sql = (
                    "SELECT TOP (?) " + select_list
                    + " FROM (" + inner + ") AS _t WHERE _t._rn = 1"
                )
            else:
                sql = (
                    "SELECT " + select_list
                    + " FROM (" + inner + ") AS _t WHERE _t._rn = 1"
                )
        else:
            sql = base_sql
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

        return self._db.query_df(sql, params=params, verbose=0)
    def fetch_measurements(
        self,
        *,
        product: str | None = None,
        serial: str | None = None,
        operation: str | None = None,
        station: str | None = None,
        date_from: str | datetime | None = None,
        date_to: str | datetime | None = None,
        measurement_name: str | None = None,
        process_mode: str | None = None,
    ) -> pd.DataFrame:
        """Measurement extract via warehouse stored procedure."""
        self._ensure()
        assert self._db is not None

        start = _parse_dt(date_from)
        end = _parse_dt(date_to)
        if end is not None and end.hour == 0 and end.minute == 0 and end.second == 0:
            end = end.replace(hour=23, minute=59, second=59)

        ops = operation.strip() if operation and operation.strip() else None

        try:
            df = self._db.fetch_measurements_df(
                product_number=product or None,
                serial_number=serial or None,
                location=station or None,
                start_time=start,
                end_time=end,
                process_mode=process_mode or None,
                operation_list=ops,
                measurement_name=measurement_name or None,
                verbose=0,
            )
        except Exception as exc:
            raise WarehouseError(str(exc) or type(exc).__name__) from exc

        return normalize_warehouse_df(df)
