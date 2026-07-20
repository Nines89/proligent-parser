"""Client per Proligent Analytics.

Gestisce login (via Edge + profilo dedicato) e query sui report
con filtri personalizzati, restituendo i dati come pandas DataFrame.

Uso tipico::

    from proligent_client import ProligentClient

    client = ProligentClient()
    client.login()

    # Query con filtri personalizzati
    df = client.query(
        station="FST_JB_PRO_001",
        date_from="2026-06-01",
        status="Pass",
    )
    print(df)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlencode

import pandas as pd
import requests
import urllib3

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page

_playwright = None


def _pw():
    """Lazy-load Playwright (heavy import; only needed for login/browser queries)."""
    global _playwright
    if _playwright is None:
        import playwright.sync_api as _playwright
    return _playwright

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_BASE_URL = "https://us70uwapp136.zam.alcatel-lucent.com:6443/Analytics"
_HOME_URL = f"{_BASE_URL}/Home/Home"
_BROWSER_DATA = Path(__file__).parent / ".proligent-browser-data"
_LOGIN_TIMEOUT_MS = 180_000

# Report parameter names (from ReportConfig/OperationRuns)
# Maps user-friendly names -> API parameter names
_PARAM_MAP = {
    "station": "stationKey",
    "stationKey": "stationKey",
    "operation": "operationKey",
    "operationKey": "operationKey",
    "product": "productKey",
    "productKey": "productKey",
    "process": "processKey",
    "processKey": "processKey",
    "status": "operationRunStatusKey",
    "operationRunStatusKey": "operationRunStatusKey",
    "serial": "productUnitIdentifierKey",
    "productUnitIdentifierKey": "productUnitIdentifierKey",
    "user": "userKey",
    "userKey": "userKey",
    "processMode": "processModeKey",
    "processModeKey": "processModeKey",
    "date_from": "operationStartDateFrom",
    "operationStartDateFrom": "operationStartDateFrom",
    "date_to": "operationStartDateTo",
    "operationStartDateTo": "operationStartDateTo",
    "end_date_from": "operationEndDateFrom",
    "operationEndDateFrom": "operationEndDateFrom",
    "end_date_to": "operationEndDateTo",
    "operationEndDateTo": "operationEndDateTo",
    "isRetest": "isRetest",
    "isLastPassage": "isLastPassage",
    "opportunityRunNumber": "opportunityRunNumber",
    "top": "top",
    "sortBy": "sortBy",
    "sortOrder": "sortOrder",
}


def _log(msg: str) -> None:
    print(f"[proligent] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Login helpers
# ---------------------------------------------------------------------------

def _is_logged_in(page: Page) -> bool:
    return "/Analytics/" in page.url and "login.microsoftonline.com" not in page.url


def _wait_and_fill(page: Page, sel: str, value: str, timeout: int = 10_000) -> bool:
    try:
        field = page.locator(sel).first
        field.wait_for(state="visible", timeout=timeout)
        field.fill(value)
        return True
    except _pw().TimeoutError:
        return False


def _click_submit(page: Page) -> None:
    for sel in ('input[type="submit"]', 'button[type="submit"]', "#idSIButton9"):
        btn = page.locator(sel).first
        try:
            btn.wait_for(state="visible", timeout=3_000)
            btn.click()
            return
        except _pw().TimeoutError:
            continue
    raise RuntimeError("Pulsante di invio non trovato nella pagina di login.")


def _handle_stay_signed_in(page: Page) -> None:
    try:
        page.locator("#idSIButton9").first.wait_for(state="visible", timeout=5_000)
        page.locator("#idSIButton9").first.click()
    except _pw().TimeoutError:
        pass


def _try_microsoft_login(page: Page, username: str, password: str) -> None:
    _log("Tentativo login Microsoft...")
    if _wait_and_fill(page, 'input[name="loginfmt"]', username):
        _log("Username inserito.")
        _click_submit(page)
        page.wait_for_load_state("networkidle", timeout=15_000)
    if _wait_and_fill(page, 'input[name="passwd"]', password):
        _log("Password inserita.")
        _click_submit(page)
        page.wait_for_load_state("networkidle", timeout=15_000)
    _handle_stay_signed_in(page)


def _wait_for_proligent(page: Page, has_creds: bool) -> None:
    if _is_logged_in(page):
        return
    _log(f"In attesa del login... (URL: {page.url})")
    if not has_creds:
        _log("Nessuna credenziale fornita – completa il login nel browser.")
    try:
        page.wait_for_url("**/Analytics/**", timeout=_LOGIN_TIMEOUT_MS)
    except _pw().TimeoutError as exc:
        if "login.microsoftonline.com" in page.url:
            raise RuntimeError(
                "Login non completato. Completa MFA nel browser "
                "oppure passa username e password."
            ) from exc
        raise RuntimeError(f"Login non completato. URL: {page.url}") from exc


def _cookies_to_session(ctx: BrowserContext) -> requests.Session:
    session = requests.Session()
    session.verify = False
    for c in ctx.cookies():
        session.cookies.set(c["name"], c["value"],
                            domain=c.get("domain"), path=c.get("path", "/"))
    return session


# ---------------------------------------------------------------------------
# HTML → DataFrame
# ---------------------------------------------------------------------------

def _extract_download_map(html: str, base_url: str = _BASE_URL) -> dict[str, str]:
    """Extract document download URLs from SSRS HTML.

    Returns a dict mapping ``"serial|operation"`` keys to download URLs.
    Scans the raw HTML for ``downloadDocuments(...)`` calls.

    Works for both the browser-rendered HTML (real quotes) and the raw
    API HTML, where quotes are HTML-encoded as ``&#39;`` / ``&#39;``.
    """
    import html as _html
    from urllib.parse import unquote

    text = _html.unescape(html)
    dl_pattern = re.compile(
        r"downloadDocuments\(\s*'([^']+)'\s*,\s*(\d+)\s*,\s*'([^']+)'\s*\)"
    )

    result: dict[str, str] = {}
    for m in dl_pattern.finditer(text):
        report_type, run_id, raw_filename = m.group(1), m.group(2), m.group(3)
        filename = unquote(raw_filename)

        url = (
            f"{base_url}/api/documents"
            f"?report={report_type}"
            f"&key={run_id}"
            f"&compressedFilename={raw_filename}"
        )

        # Filename format: SERIAL-PRODUCT-OPERATION-PASSAGE.zip
        parts = filename.replace(".zip", "").split("-", 2)
        if len(parts) >= 3:
            serial = parts[0]
            operation = parts[2].rsplit("-", 1)[0]
            key = f"{serial}|{operation}"
            result[key] = url

    _log(f"  Download links trovati: {len(result)}")
    return result


# Matches the product path in the SSRS anchor's `title` attribute, e.g.
# title="Root Product/OND/PROTEUS/SSY/CTL/UNC4/3TK00728AA\nGo to Measurements"
_PRODUCT_TITLE_RE = re.compile(
    r'title="Root Product/([^"]*?)(?:\r?\n|&#10;|&#xA;|")',
    re.IGNORECASE,
)


def _extract_product_paths(html: str) -> dict[str, str]:
    """Extract a ``product_code -> full_hierarchy_path`` map from SSRS HTML.

    The product cell exposes the full hierarchy path in the anchor `title`
    attribute (``Root Product/.../MNEMONIC/CODE``). The last path element is
    the product code shown in the table; the full path is what Proligent uses
    as the ``ProductDW`` filter value.
    """
    result: dict[str, str] = {}
    for m in _PRODUCT_TITLE_RE.finditer(html):
        tail = m.group(1).strip().strip("/")
        parts = [p for p in tail.split("/") if p]
        if len(parts) < 2:
            continue
        code = parts[-1]
        if code:
            result.setdefault(code, "Root Product/" + tail)
    return result


def _extract_product_mnemonics(html: str) -> dict[str, str]:
    """Extract a ``product_code -> mnemonic`` map from SSRS HTML.

    The mnemonic is the penultimate element of the product hierarchy path.
    """
    result: dict[str, str] = {}
    for code, full in _extract_product_paths(html).items():
        parts = [p for p in full.split("/") if p]
        if len(parts) >= 2:
            result[code] = parts[-2]
    return result


def _find_product_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if str(col).strip().lower() == "product":
            return str(col)
    for col in df.columns:
        if "product" in str(col).lower():
            return str(col)
    return None


def _apply_product_mnemonics(
    df: pd.DataFrame, product_map: dict[str, str]
) -> pd.DataFrame:
    """Prefix the product column with its mnemonic (``MNEMONIC -> CODE``)."""
    if df.empty or not product_map:
        return df
    col = _find_product_column(df)
    if col is None:
        return df

    def _fmt(val: Any) -> Any:
        if pd.isna(val):
            return val
        code = str(val).strip()
        mnemonic = product_map.get(code)
        if not mnemonic or mnemonic == code or " -> " in code:
            return val
        return f"{mnemonic} -> {code}"

    df[col] = df[col].map(_fmt)
    return df


def _apply_download_urls(df: pd.DataFrame, dl_map: dict[str, str]) -> pd.DataFrame:
    """Attach a hidden ``_download_url`` column matched by serial + operation."""
    if df.empty or not dl_map:
        return df
    sn_col = next((c for c in df.columns if "serial" in str(c).lower()), None)
    op_col = next(
        (c for c in df.columns if str(c).lower() == "operation"), None
    )
    if not sn_col or not op_col:
        return df
    df["_download_url"] = df.apply(
        lambda r: dl_map.get(f"{r[sn_col]}|{r[op_col]}", ""), axis=1
    )
    matched = (df["_download_url"] != "").sum()
    _log(f"Download abbinati: {matched}/{len(df)}")
    return df


def _build_unit_view_bookmark(serial: str, product_full_path: str) -> str:
    """Build the "Unit Results View" bookmark payload for a unit.

    The raw report HTML does not embed this navigation (SSRS adds it
    client-side), so we reconstruct it from the serial number and the product
    hierarchy path, exactly as Proligent would.
    """
    return json.dumps({
        "TargetReport": "UnitResultsView",
        "Filter": [
            {"FilterName": "SerialNumberDW", "FilterValue": f"All/{serial}"},
            {"FilterName": "ProductDW", "FilterValue": product_full_path},
        ],
    })


def _apply_unit_view(
    df: pd.DataFrame, product_path_map: dict[str, str]
) -> pd.DataFrame:
    """Attach a hidden ``_unit_view`` column built from serial + product path."""
    if df.empty or not product_path_map:
        _log("Unit Results View: nessun percorso prodotto disponibile, skip.")
        return df
    sn_col = next(
        (c for c in df.columns if "serial" in str(c).lower()), None
    )
    prod_col = _find_product_column(df)
    if sn_col is None or prod_col is None:
        _log("Unit Results View: colonna serial/prodotto non trovata, skip.")
        return df

    def _mk(row: pd.Series) -> str:
        serial, prod = row[sn_col], row[prod_col]
        if pd.isna(serial) or pd.isna(prod):
            return ""
        serial = str(serial).strip()
        prod = str(prod).strip()
        # Product cell may already be "MNEMONIC -> CODE"; take the code.
        code = prod.split(" -> ")[-1].strip() if " -> " in prod else prod
        full = product_path_map.get(code)
        if not serial or not full:
            return ""
        return _build_unit_view_bookmark(serial, full)

    df["_unit_view"] = df.apply(_mk, axis=1)
    matched = (df["_unit_view"] != "").sum()
    _log(f"Unit Results View costruiti: {matched}/{len(df)}")
    return df


def _find_edge_executable() -> str | None:
    """Locate the Microsoft Edge executable on Windows."""
    candidates = [
        os.path.expandvars(
            r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
        ),
        os.path.expandvars(
            r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
        ),
        os.path.expandvars(
            r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"
        ),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return shutil.which("msedge")


def _parse_report_html(html: str, dump_debug: bool = False) -> pd.DataFrame:
    """Extract the data table(s) from SSRS-rendered HTML.

    SSRS can split results across multiple <table> elements (page breaks).
    We concatenate all candidate tables that share the same column structure.
    """
    if dump_debug:
        debug_path = Path(__file__).parent / "_debug_report.html"
        debug_path.write_text(html, encoding="utf-8")
        _log(f"HTML debug salvato in {debug_path}")

    dfs = pd.read_html(StringIO(html))
    if not dfs:
        return pd.DataFrame()

    candidates = [df for df in dfs if df.shape[1] >= 10]
    if not candidates:
        candidates = [df for df in dfs if df.shape[1] >= 3]
    if not candidates:
        return pd.DataFrame()

    def _normalize(df: pd.DataFrame) -> pd.DataFrame:
        header_idx = None
        for r in range(min(10, len(df))):
            row_vals = [str(v) for v in df.iloc[r].dropna().tolist()]
            if any("Serial Number" in v for v in row_vals):
                header_idx = r
                break
        if header_idx is not None:
            cols = [str(c) for c in df.iloc[header_idx].tolist()]
            seen: dict[str, int] = {}
            deduped: list[str] = []
            for c in cols:
                if c in seen:
                    seen[c] += 1
                    deduped.append(f"{c}_{seen[c]}")
                else:
                    seen[c] = 0
                    deduped.append(c)
            df.columns = deduped
            df = df.iloc[header_idx + 1:]
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        return df

    ref = max(candidates, key=lambda d: d.shape[0])
    ref_cols = ref.shape[1]

    compatible = [_normalize(df) for df in candidates if df.shape[1] == ref_cols]
    if not compatible:
        compatible = [_normalize(ref)]

    df = pd.concat(compatible, ignore_index=True)
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    non_null_counts = df.notna().sum(axis=1)
    min_required = max(1, len(df.columns) // 5)
    df = df[non_null_counts >= min_required]

    return df.reset_index(drop=True)


def _extract_record_count(html: str) -> int | None:
    m = re.search(r"(\d+)\s+(?:operation|sequence|unit).*?found", html, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _is_uuid(s: str) -> bool:
    return bool(re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        s, re.IGNORECASE,
    ))



def _find_time_column(df: pd.DataFrame) -> str | None:
    """Find the best datetime column for cursor-based pagination."""
    for col in df.columns:
        low = str(col).lower()
        if "start time" in low or "start_time" in low:
            return str(col)
    for col in df.columns:
        low = str(col).lower()
        if "time" in low or "date" in low:
            return str(col)
    return None


def _extract_cursor_time(df: pd.DataFrame, time_col: str) -> str | None:
    """Get the oldest timestamp from the batch to use as cursor for the next query.

    Subtracts 1 second to avoid re-fetching boundary records.
    Ignores obviously bogus dates (before 2010) to avoid invalid cursors.
    """
    try:
        times = pd.to_datetime(df[time_col], errors="coerce", utc=True)
        valid = times.dropna()
        cutoff = pd.Timestamp("2010-01-01", tz="UTC")
        valid = valid[valid >= cutoff]
        if valid.empty:
            return None
        oldest = valid.min() - pd.Timedelta(seconds=1)
        return oldest.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class ProligentClient:
    """Client per interrogare Proligent Analytics.

    Parameters
    ----------
    base_url : str
        URL base di Proligent Analytics.
    browser_data : Path | str
        Directory per il profilo browser Playwright.
    """

    def __init__(
        self,
        base_url: str = _BASE_URL,
        browser_data: Path | str = _BROWSER_DATA,
        query_timeout: int = 300,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.browser_data = Path(browser_data)
        self._session: requests.Session | None = None
        # Read timeout (seconds) for the heavy report-rendering calls; large
        # queries can take a few minutes to render server-side.
        self.query_timeout = query_timeout

    # -- Login ---------------------------------------------------------------

    def login(
        self,
        username: str | None = None,
        password: str | None = None,
        headless: bool = False,
    ) -> None:
        """Apre Edge, naviga a Proligent, estrae i cookie di sessione."""
        self.browser_data.mkdir(parents=True, exist_ok=True)
        _log(f"Profilo browser: {self.browser_data}")

        _OFFSCREEN = ["--window-position=-32000,-32000", "--window-size=1,1"]

        with _pw().sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=str(self.browser_data),
                channel="msedge",
                headless=headless,
                ignore_https_errors=True,
                args=_OFFSCREEN if headless else [],
            )
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

            _log("Navigazione verso Proligent...")
            home = f"{self.base_url}/Home/Home"
            try:
                resp = page.goto(home, wait_until="domcontentloaded", timeout=60_000)
                if resp:
                    _log(f"HTTP {resp.status}")
            except _pw().TimeoutError:
                _log(f"Timeout navigazione. URL: {page.url}")

            if _is_logged_in(page):
                _log("Già autenticato.")
            else:
                if username and password:
                    _try_microsoft_login(page, username, password)
                _wait_for_proligent(page, has_creds=bool(username and password))

            self._session = _cookies_to_session(ctx)
            _log(f"Login OK – {len(self._session.cookies)} cookie.")
            ctx.close()

    def close(self) -> None:
        """Noop – il browser viene chiuso dopo ogni operazione."""

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            raise RuntimeError("Esegui client.login() prima di fare query.")
        return self._session

    # -- Browser-based query (Discovery pagination) --------------------------

    def query_via_browser(self, shortcut_uuid: str) -> pd.DataFrame:
        """Recupera tutti i record di uno shortcut navigando la pagina Discovery.

        Crea un'istanza Playwright headless dedicata usando lo stesso
        profilo browser (i cookie di sessione sono gia su disco dal login).
        """
        with _pw().sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=str(self.browser_data),
                channel="msedge",
                headless=True,
                ignore_https_errors=True,
                args=["--window-position=-32000,-32000", "--window-size=1,1"],
            )
            page = ctx.new_page()
            try:
                return self._scrape_discovery_pages(page, shortcut_uuid)
            finally:
                page.close()
                ctx.close()

    def _scrape_discovery_pages(self, page: Page, uuid: str) -> pd.DataFrame:
        url = f"{self.base_url}/Discovery?id={uuid}&viewmode=table"
        _log(f"Navigazione Discovery: {url}")
        page.goto(url, wait_until="networkidle", timeout=90_000)

        # Wait for the SSRS report viewer to appear
        try:
            page.locator("#oReportDiv").wait_for(state="attached", timeout=60_000)
        except _pw().TimeoutError:
            _log("Timeout: il report SSRS non si e' caricato.")
            return pd.DataFrame()

        # Read page count
        page_count = 1
        pager = page.locator("span.page-count-info")
        if pager.count() > 0:
            text = pager.first.text_content() or ""
            m = re.search(r"(\d+)", text)
            if m:
                page_count = int(m.group(1))
        _log(f"Discovery: {page_count} pagine trovate.")

        all_dfs: list[pd.DataFrame] = []
        all_dl_maps: dict[str, str] = {}
        product_map: dict[str, str] = {}
        product_path_map: dict[str, str] = {}

        for pg in range(1, page_count + 1):
            if pg > 1:
                btn = page.locator(
                    f'li.wijmo-wijpager-button[title="{pg}"] a'
                )
                if btn.count() == 0:
                    btn = page.locator(
                        f'li.wijmo-wijpager-button[aria-label="{pg}"] a'
                    )
                if btn.count() > 0:
                    _log(f"  Pagina {pg}/{page_count}: click...")
                    btn.first.click()
                    page.wait_for_load_state("networkidle", timeout=60_000)
                    # Wait for the report to re-render
                    page.locator("#oReportDiv").wait_for(
                        state="attached", timeout=30_000
                    )
                    page.wait_for_timeout(1_000)
                else:
                    _log(f"  Pagina {pg}: pulsante non trovato, skip.")
                    continue

            html = page.locator("#oReportDiv").inner_html()
            if not html:
                _log(f"  Pagina {pg}: HTML vuoto.")
                continue

            df = _parse_report_html(html)
            _log(f"  Pagina {pg}/{page_count}: {len(df)} righe.")
            if not df.empty:
                dl_map = _extract_download_map(html, self.base_url)
                all_dl_maps.update(dl_map)
                product_map.update(_extract_product_mnemonics(html))
                product_path_map.update(_extract_product_paths(html))
                all_dfs.append(df)

        if not all_dfs:
            return pd.DataFrame()

        combined = pd.concat(all_dfs, ignore_index=True).drop_duplicates()

        # Drop noise columns (all-NaN, "nan" headers, unnamed/duplicate _N cols)
        drop_cols = [
            c for c in combined.columns
            if (str(c).lower() == "nan"
                or combined[c].isna().all()
                or re.match(r"^nan_\d+$", str(c), re.IGNORECASE))
        ]
        if drop_cols:
            combined = combined.drop(columns=drop_cols)

        # Drop noise rows: require "Serial Number" (or first col) to be non-null
        key_col = None
        for c in combined.columns:
            if "serial" in str(c).lower():
                key_col = c
                break
        if key_col is None and len(combined.columns) > 0:
            key_col = combined.columns[0]
        if key_col is not None:
            combined = combined[combined[key_col].notna()].reset_index(drop=True)

        combined = combined.drop_duplicates().reset_index(drop=True)

        # Match download URLs to cleaned rows
        combined = _apply_download_urls(combined, all_dl_maps)

        combined = _apply_product_mnemonics(combined, product_map)
        combined = _apply_unit_view(combined, product_path_map)

        _log(f"Discovery totale: {len(combined)} record univoci.")
        return combined

    # -- Low-level API -------------------------------------------------------

    def _post(self, path: str, *, timeout: int | tuple[int, int] = 120,
              **kwargs) -> requests.Response:
        return self.session.post(
            f"{self.base_url}{path}", timeout=timeout, **kwargs
        )

    def _get(self, path: str, **kwargs) -> requests.Response:
        return self.session.get(
            f"{self.base_url}{path}", timeout=60, **kwargs
        )

    # -- Unit Results View ---------------------------------------------------

    def _resolve_filter_items(
        self, filter_name: str, full_name: str
    ) -> list[dict[str, Any]]:
        """Resolve a filter value (by full name) into its filter items.

        Mirrors the browser's ``FilterItem/{name}/Search`` call used when
        building a navigation context.
        """
        body = urlencode({"$filter": f"fullName eq '{full_name}'"})
        r = self._post(
            f"/api/FilterItem/{quote(filter_name)}/Search/",
            data=body,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
        )
        r.raise_for_status()
        data: Any = r.json()
        if isinstance(data, dict):
            data = data.get("data") or data.get("items") or []
        fields = ("id", "key", "name", "fullName", "level", "isLeaf")
        items: list[dict[str, Any]] = []
        for it in data or []:
            if isinstance(it, dict):
                items.append({k: it[k] for k in fields if k in it})
        return items

    @staticmethod
    def _parse_context_id(resp: requests.Response) -> str:
        try:
            data = resp.json()
        except ValueError:
            return resp.text.strip().strip('"')
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            for k in ("contextId", "id", "ContextId", "Id", "context"):
                if k in data:
                    return str(data[k])
        return str(data).strip('"')

    def build_unit_view_url(self, unit_view: str | dict) -> str:
        """Build the shareable ``Discovery?context=…`` URL for a unit.

        Replicates the browser's "open in a new tab" flow: resolve the
        bookmark filters, persist a navigation context server-side, then
        return the URL that renders that context.
        """
        params = json.loads(unit_view) if isinstance(unit_view, str) else unit_view
        filters = params.get("Filter") or []
        if isinstance(filters, dict):
            filters = [filters]

        report_filters: list[dict[str, Any]] = []
        for f in filters:
            name = f.get("FilterName")
            value = f.get("FilterValue")
            if not name or value is None:
                continue
            items = self._resolve_filter_items(name, str(value))
            report_filters.append({"name": name, "filterItems": items})

        global_context = {
            "filterContexts": [],
            "reportContext": {
                "reportName": params.get("TargetReport", "UnitResultsView"),
                "reportCaption": None,
                "linkedReportName": None,
                "selectors": [],
                "filters": report_filters,
            },
            "dateRange": {"code": None, "caption": None, "range": None},
            "sourcePrimaryDateFilterName": None,
        }

        _log(f"Creazione contesto navigazione per {params.get('TargetReport')}…")
        r = self._post(
            "/api/GlobalContext",
            data=json.dumps(global_context),
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        r.raise_for_status()
        context_id = self._parse_context_id(r)
        if not context_id:
            raise RuntimeError("Il server non ha restituito un context id valido.")
        return f"{self.base_url}/Discovery?context={quote(str(context_id))}"

    def _sync_viewer_profile(self, viewer_dir: Path) -> None:
        """Copy the auth cookies from the main profile into the viewer profile.

        The standalone viewer Edge must use a *separate* ``user-data-dir`` from
        the one Playwright drives (login / paginated queries); otherwise the two
        Edge instances fight over the profile lock and Playwright fails with
        "Target page, context or browser has been closed". Copying the cookies
        (and the ``Local State`` that holds their encryption key) keeps the
        viewer authenticated without a second login.
        """
        src = self.browser_data
        try:
            (viewer_dir / "Default" / "Network").mkdir(parents=True, exist_ok=True)
            local_state = src / "Local State"
            if local_state.exists():
                shutil.copy2(local_state, viewer_dir / "Local State")
            for base in (src / "Default" / "Network", src / "Default"):
                for fn in ("Cookies", "Cookies-journal"):
                    s = base / fn
                    if s.exists():
                        shutil.copy2(s, viewer_dir / "Default" / "Network" / fn)
                if (base / "Cookies").exists():
                    break
        except OSError as exc:
            _log(f"Sync profilo viewer non riuscito ({exc}); uso i cookie esistenti.")

    def open_unit_view(self, unit_view: str | dict) -> str:
        """Open the Unit Results View in a standalone Edge window.

        Uses a dedicated viewer profile (separate from the Playwright one) so it
        never collides with login / query operations, and reuses the session by
        copying the auth cookies over. Returns the opened URL.
        """
        url = self.build_unit_view_url(unit_view)
        edge = _find_edge_executable()
        if edge:
            viewer_dir = self.browser_data.parent / f"{self.browser_data.name}-viewer"
            self._sync_viewer_profile(viewer_dir)
            _log(f"Apertura in Edge: {url}")
            subprocess.Popen(
                [edge, f"--user-data-dir={viewer_dir}", url],
                close_fds=True,
            )
        else:
            import webbrowser

            _log("Edge non trovato, apertura nel browser predefinito.")
            webbrowser.open(url)
        return url

    # -- Query ---------------------------------------------------------------

    def query(
        self,
        report: str = "OperationRuns",
        *,
        station: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        operation: str | None = None,
        product: str | None = None,
        serial: str | None = None,
        top: int | None = None,
        **extra_filters: str,
    ) -> pd.DataFrame:
        """Esegue una query su Proligent e ritorna un DataFrame.

        Parameters
        ----------
        report : str
            Nome del report built-in (es. ``"OperationRuns"``,
            ``"SequenceRuns"``, ``"Activity"``, ``"CycleTime"``,
            ``"Yield"``) oppure UUID di uno shortcut.
        station : str, optional
            Chiave o nome della stazione (es. ``"92671"`` o
            ``"FST_JB_PRO_001"``).
        date_from : str, optional
            Data inizio (es. ``"2026-06-01"``).
        date_to : str, optional
            Data fine (es. ``"2026-06-30"``).
        status : str, optional
            Filtro status (es. ``"Pass"``, ``"Fail"``).
        operation : str, optional
            Chiave operazione.
        product : str, optional
            Chiave prodotto.
        serial : str, optional
            Serial number.
        top : int, optional
            Numero massimo di record.
        **extra_filters
            Parametri aggiuntivi (nomi dal ReportConfig).

        Returns
        -------
        pd.DataFrame
        """
        params: dict[str, str] = {
            "ReportName": report,
            "ReportFlavor": "1",
            "Height": "500000",
            "Width": "10000",
            "sortBy": "Start Time",
            "sortOrder": "DESC",
        }

        # Map user-friendly kwargs to API parameter names
        local_filters = {
            "station": station, "date_from": date_from, "date_to": date_to,
            "status": status, "operation": operation, "product": product,
            "serial": serial, "top": str(top) if top else None,
        }
        for key, value in {**local_filters, **extra_filters}.items():
            if value is None:
                continue
            api_name = _PARAM_MAP.get(key, key)
            params[api_name] = str(value)

        filter_desc = {k: v for k, v in params.items()
                       if k not in ("ReportName", "ReportFlavor", "Height", "Width")}
        if filter_desc:
            _log(f"Query {report} con filtri: {filter_desc}")
        else:
            _log(f"Query {report} (nessun filtro)")

        r = self._post(
            "/api/ReportInstanceRendering/Shortcut",
            data=urlencode(params),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=self.query_timeout,
        )
        r.raise_for_status()

        result = r.json()
        html = result["RenderResult"]["HtmlContent"]
        num_pages = result["RenderResult"].get("NumPages", 1)

        total = _extract_record_count(html)
        df = _parse_report_html(html)
        rendered = len(df)
        product_map = _extract_product_mnemonics(html)
        product_path_map = _extract_product_paths(html)
        dl_map = _extract_download_map(html, self.base_url)

        _log(f"Risultato: {total or '?'} totali, {rendered} renderizzati, {num_pages} pagine.")

        if num_pages <= 1 or rendered == 0:
            df = _apply_product_mnemonics(df, product_map)
            df = _apply_unit_view(df, product_path_map)
            return _apply_download_urls(df, dl_map)

        # Shortcut UUIDs: use browser-based Discovery pagination
        if _is_uuid(report):
            _log(
                f"Shortcut con {num_pages} pagine: "
                "paginazione via Discovery browser..."
            )
            return self.query_via_browser(report)

        # --- Cursor-based pagination for named reports ---
        time_col = _find_time_column(df)
        if time_col is None:
            _log("Nessuna colonna tempo trovata per la paginazione automatica.")
            df = _apply_product_mnemonics(df, product_map)
            df = _apply_unit_view(df, product_path_map)
            return _apply_download_urls(df, dl_map)

        _log(f"Paginazione automatica usando colonna '{time_col}'…")
        all_dfs = [df]
        collected = rendered
        last_batch = df
        max_iterations = 20
        expected = total if total else num_pages * rendered

        for iteration in range(max_iterations):
            cursor = _extract_cursor_time(last_batch, time_col)
            if cursor is None:
                _log("Impossibile estrarre cursore tempo, stop.")
                break

            page_params = dict(params)
            page_params["operationStartDateTo"] = cursor
            _log(f"  Pagina {iteration + 2}: date_to={cursor}")

            rp = self._post(
                "/api/ReportInstanceRendering/Shortcut",
                data=urlencode(page_params),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.query_timeout,
            )
            rp.raise_for_status()
            page_html = rp.json()["RenderResult"]["HtmlContent"]
            page_df = _parse_report_html(page_html, dump_debug=False)
            product_map.update(_extract_product_mnemonics(page_html))
            product_path_map.update(_extract_product_paths(page_html))
            dl_map.update(_extract_download_map(page_html, self.base_url))

            if page_df.empty:
                _log("  Pagina vuota, stop.")
                break

            prev_count = collected
            combined = pd.concat(all_dfs + [page_df], ignore_index=True)
            combined = combined.drop_duplicates()
            collected = len(combined)
            new_rows = collected - prev_count

            _log(f"  +{new_rows} nuove righe (totale: {collected})")

            if new_rows == 0:
                _log("  Nessuna nuova riga, stop.")
                break

            all_dfs = [combined]
            last_batch = page_df

            if collected >= expected:
                _log(f"Raccolti tutti i {collected} record.")
                break

        df = pd.concat(all_dfs, ignore_index=True).drop_duplicates()
        df = _apply_product_mnemonics(df, product_map)
        df = _apply_unit_view(df, product_path_map)
        df = _apply_download_urls(df, dl_map)
        _log(f"Totale finale: {len(df)} record univoci.")
        return df.reset_index(drop=True)

    # -- Shortcut-based query (backward compatible) --------------------------

    def query_report(
        self,
        report_name: str,
        filters: dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """Esegue un report shortcut (per compatibilità)."""
        return self.query(report_name, **(filters or {}))

    # -- Metadata ------------------------------------------------------------

    def get_report_config(self, report_name: str) -> dict:
        """Ritorna la configurazione di un report (filtri, parametri)."""
        r = self._get(f"/api/ReportConfig/{report_name}")
        r.raise_for_status()
        return r.json()

    def get_available_reports(self) -> list[dict]:
        """Ritorna l'elenco di tutti i report disponibili."""
        r = self._get("/api/ReportSection/")
        r.raise_for_status()
        sections = r.json()
        reports = []
        for category in sections:
            cat_name = category.get("caption", "")
            for section in category.get("sections", []):
                for rep in section.get("report", []):
                    if rep.get("visible", True):
                        reports.append({
                            "category": cat_name,
                            "section": section.get("caption", ""),
                            "name": rep["name"],
                            "caption": rep.get("caption", ""),
                            "description": rep.get("description", ""),
                            "is_shortcut": rep.get("isReportShortcut", False),
                        })
        return reports

    def get_filter_catalog(self) -> list[dict]:
        """Ritorna il catalogo completo dei filtri disponibili."""
        r = self._get("/api/FilterCatalogV2")
        r.raise_for_status()
        return r.json()
