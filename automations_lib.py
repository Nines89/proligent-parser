"""Helpers for user-defined automation scripts.

Layout (created at runtime, not committed)::

    automations/
        <slug>/                 # one folder per automation (tab name)
            meta.json           # {"name": "Display Name"}
            src/
                main.py         # entry point: run(df, files_dir)
            files/
                plots/          # charts saved by the automation (shown in the GUI)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

AUTOMATIONS_ROOT = Path(__file__).resolve().parent / "automations"
_META_FILE = "meta.json"
PLOT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif")

_TEMPLATE = '''\
"""Automation: {name}

==============================================================================
HOW THE APP RUNS THIS FILE
==============================================================================
1. Click **Run** on this automation tab.
2. The app loads ``main.py`` and calls::

       run(df, files_dir)

3. Arguments
   * ``df``        – pandas DataFrame = rows visible in the **Dati** tab
                     (date filters + Excel-style grid filters already applied).
   * ``files_dir`` – Path to this automation\'s ``files/`` folder
                     (downloaded reports, CSV exports, charts, …).

4. Console
   * ``print(...)``          → blue/black lines in the Output panel (stdout)
   * messages on stderr      → orange lines
   * uncaught exceptions     → red traceback

5. Charts (IMPORTANT – do not rely on interactive popups)
   The automation runs in a background thread, so ``plt.show()`` windows are
   unreliable. Instead **save** images under ``files/plots/``:

       fig, ax = plt.subplots()
       ax.bar([\"Pass\", \"Fail\"], [10, 2])
       save_plot(fig, files_dir, \"status_counts\")   # → files/plots/status_counts.png

   After Run, the GUI shows every image found in ``files/plots/``.
   Double-click a thumbnail to open it in the system viewer.

6. Extra Python modules
   Put helpers next to this file (same ``src/`` folder), e.g. ``logic.py``,
   then::

       from logic import my_helper

==============================================================================
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Optional – only needed when you draw charts:
#   pip install matplotlib
try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None  # type: ignore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def list_files(files_dir: Path, *, pattern: str = "*") -> list[Path]:
    """Return the files inside ``files_dir`` as a sorted list of Paths.

    Examples
    --------
    all_files = list_files(files_dir)
    zips_only = list_files(files_dir, pattern="*.zip")

    for path in list_files(files_dir):
        print(path.name, path.stat().st_size)
    """
    folder = Path(files_dir)
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.glob(pattern) if p.is_file())


def plots_dir(files_dir: Path) -> Path:
    """Return ``files/plots/``, creating it if needed."""
    d = Path(files_dir) / "plots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_plot(fig, files_dir: Path, name: str = "plot") -> Path:
    """Save a matplotlib Figure into ``files/plots/<name>.png`` and return the path.

    The GUI gallery picks up anything saved here after **Run**.

    Example
    -------
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    save_plot(fig, files_dir, "my_trend")
    """
    if fig is None:
        raise ValueError("fig is None – create a matplotlib figure first.")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name).strip("_")
    safe = safe or "plot"
    out = plots_dir(files_dir) / f"{{safe}}.png"
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(f"[plot saved] {{out}}")
    try:
        import matplotlib.pyplot as _plt
        _plt.close(fig)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# Pandas quick guide (for beginners)
# ---------------------------------------------------------------------------
# A DataFrame is a table: rows = records, columns = fields.
#
# Inspect
#   print(df.shape)             # (n_rows, n_columns)
#   print(df.columns.tolist())  # exact column names (spaces matter!)
#   print(df.head())
#   print(df["Status"].value_counts())
#
# Filter (always .copy() if you keep the result)
#   fails = df[df["Status"].astype(str).str.lower() == "fail"].copy()
#   mask = (df["Status"] == "Fail") & (df["Location"].astype(str).str.contains("FST", na=False))
#   subset = df[mask].copy()
#
# Export tables
#   fails.to_csv(files_dir / "fails.csv", index=False, encoding="utf-8-sig")
#
# Charts – save into files/plots (shown in the GUI)
#   if plt is not None and "Status" in df.columns:
#       counts = df["Status"].astype(str).value_counts()
#       fig, ax = plt.subplots()
#       ax.bar(counts.index.astype(str), counts.values)
#       ax.set_title("Status distribution")
#       save_plot(fig, files_dir, "status_distribution")
# ---------------------------------------------------------------------------


def run(df: pd.DataFrame, files_dir: Path) -> None:
    """Entry point called by the app with the filtered Dati tab data."""
    # --- inspect --------------------------------------------------------------
    # print("rows:", len(df))
    # print("columns:", df.columns.tolist())
    # print(df.head())

    # --- list downloaded report files -----------------------------------------
    # for path in list_files(files_dir):
    #     print("file:", path.name)

    # --- filter + CSV ---------------------------------------------------------
    # if "Status" in df.columns:
    #     fails = df[df["Status"].astype(str).str.lower() == "fail"].copy()
    #     out = files_dir / "fails.csv"
    #     fails.to_csv(out, index=False, encoding="utf-8-sig")
    #     print(f"wrote {{out}} ({{len(fails)}} rows)")

    # --- chart (requires: pip install matplotlib) -----------------------------
    # if plt is not None and "Status" in df.columns:
    #     counts = df["Status"].astype(str).value_counts()
    #     fig, ax = plt.subplots(figsize=(6, 4))
    #     ax.bar(counts.index.astype(str), counts.values)
    #     ax.set_title("Status distribution")
    #     ax.tick_params(axis="x", rotation=30)
    #     save_plot(fig, files_dir, "status_distribution")
    # elif plt is None:
    #     print("matplotlib not installed – skip charts")

    # TODO: implement your automation
    pass
'''


def ensure_dirs() -> None:
    AUTOMATIONS_ROOT.mkdir(parents=True, exist_ok=True)


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "_", s).strip("_")
    return s or "automation"


def _read_meta(root: Path) -> dict[str, Any]:
    meta = root / _META_FILE
    if not meta.is_file():
        return {}
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _read_name(root: Path) -> str:
    data = _read_meta(root)
    name = str(data.get("name", "")).strip()
    if name:
        return name
    script = root / "src" / "main.py"
    if script.is_file():
        try:
            head = script.read_text(encoding="utf-8", errors="ignore")[:200]
            m = re.search(r'"""Automation:\s*(.+?)\s*(?:\n|""")', head)
            if m:
                return m.group(1).strip()
        except OSError:
            pass
    return root.name.replace("_", " ")


def _write_meta(root: Path, name: str, **extra: Any) -> None:
    data = {**_read_meta(root), "name": name, **extra}
    (root / _META_FILE).write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def ensure_automation_layout(root: Path, *, name: str | None = None) -> dict[str, Any]:
    """Make sure ``root`` has src/, files/, src/main.py and meta.json."""
    display = (name or _read_name(root)).strip() or root.name
    src_dir = root / "src"
    files_dir = root / "files"
    src_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)
    (files_dir / "plots").mkdir(parents=True, exist_ok=True)

    script = src_dir / "main.py"
    if not script.is_file():
        script.write_text(_TEMPLATE.format(name=display), encoding="utf-8")

    meta = root / _META_FILE
    if not meta.is_file():
        _write_meta(root, display)

    meta_data = _read_meta(root)
    return {
        "name": _read_name(root),
        "slug": root.name,
        "root": root.resolve(),
        "script": script.resolve(),
        "files_dir": files_dir.resolve(),
        "download_documents": bool(meta_data.get("download_documents", False)),
    }


def list_plot_images(files_dir: Path) -> list[Path]:
    """Return image files under ``files/plots/`` (GUI gallery)."""
    plots = Path(files_dir) / "plots"
    if not plots.is_dir():
        return []
    found: list[Path] = []
    for p in sorted(plots.iterdir(), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in PLOT_EXTENSIONS:
            found.append(p.resolve())
    return found


def list_automations() -> list[dict[str, Any]]:
    """One entry per subfolder of ``automations/`` (same level as temp_test)."""
    ensure_dirs()
    found: list[dict[str, Any]] = []
    for child in sorted(AUTOMATIONS_ROOT.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        found.append(ensure_automation_layout(child))
    return found


def delete_automation(root: Path) -> None:
    """Remove an automation folder from disk."""
    import shutil

    root = Path(root)
    if not root.exists():
        return
    resolved = root.resolve()
    base = AUTOMATIONS_ROOT.resolve()
    if base not in resolved.parents and resolved != base:
        raise ValueError(f"Refusing to delete outside automations/: {resolved}")
    if resolved.parent != base:
        raise ValueError(f"Refusing to delete nested path: {resolved}")
    shutil.rmtree(resolved)


def create_automation(
    name: str,
    *,
    download_documents: bool = False,
) -> dict[str, Any]:
    """Create a new sibling folder under ``automations/`` with src/ + files/."""
    name = name.strip()
    if not name:
        raise ValueError("Il nome dell'automazione non può essere vuoto.")

    ensure_dirs()
    slug = slugify(name)
    root = AUTOMATIONS_ROOT / slug
    n = 2
    while root.exists():
        root = AUTOMATIONS_ROOT / f"{slug}_{n}"
        n += 1

    root.mkdir(parents=True, exist_ok=False)
    info = ensure_automation_layout(root, name=name)
    _write_meta(root, name, download_documents=bool(download_documents))
    info["name"] = name
    info["download_documents"] = bool(download_documents)
    return info
