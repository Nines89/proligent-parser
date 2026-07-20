"""Entry point per Proligent Parser.

Esempi::

    # Query su OperationRuns senza filtri
    py main.py

    # Filtra per stazione
    py main.py --station 92671

    # Filtra per stazione e periodo
    py main.py --station 92671 --date-from 2026-06-01 --date-to 2026-06-30

    # Filtra per status
    py main.py --station 92671 --status Pass

    # Salva in CSV
    py main.py --station 92671 --csv output.csv

    # Lista report disponibili
    py main.py --list-reports

    # Info su un report specifico
    py main.py --info OperationRuns
"""

import argparse
import getpass
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from proligent_client import ProligentClient

theme = Theme({
    "title": "bold cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "info": "dim cyan",
    "key": "bold white",
    "value": "white",
})

console = Console(theme=theme)


def _banner() -> Panel:
    text = Text()
    text.append("PROLIGENT", style="bold cyan")
    text.append("  Parser", style="dim white")
    return Panel(text, border_style="cyan", padding=(0, 2))


def _show_reports(client: ProligentClient) -> int:
    with console.status("[info]Caricamento report disponibili…[/]"):
        reports = client.get_available_reports()

    if not reports:
        console.print("[warning]Nessun report trovato.[/]")
        return 1

    table = Table(
        title="Report disponibili",
        title_style="title",
        border_style="dim cyan",
        header_style="bold white",
        show_lines=False,
        pad_edge=True,
        expand=True,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Sezione", style="info", ratio=1)
    table.add_column("Nome", style="key", ratio=1)
    table.add_column("Descrizione", style="value", ratio=2)
    table.add_column("", width=3, justify="center")

    current_section = ""
    for i, r in enumerate(reports, 1):
        section = f"{r['category']} › {r['section']}"
        display_section = section if section != current_section else ""
        current_section = section
        shortcut = "⚡" if r["is_shortcut"] else ""
        table.add_row(str(i), display_section, r["name"], r["caption"], shortcut)

    console.print()
    console.print(table)
    console.print(f"\n  [info]Totale:[/] [success]{len(reports)}[/] report\n")
    return 0


def _show_info(client: ProligentClient, report_name: str) -> int:
    with console.status(f"[info]Caricamento configurazione di [key]{report_name}[/key]…[/]"):
        config = client.get_report_config(report_name)

    info_table = Table(
        show_header=False,
        border_style="dim cyan",
        pad_edge=True,
        box=None,
    )
    info_table.add_column("Campo", style="info", width=14, justify="right")
    info_table.add_column("Valore", style="key")

    info_table.add_row("Report", config.get("caption", "?"))
    info_table.add_row("Nome", config.get("name", "?"))
    info_table.add_row("Descrizione", config.get("description", "") or "–")
    csv_flag = config.get("allowCsvExport", "?")
    csv_style = "success" if csv_flag else "warning"
    info_table.add_row("Export CSV", Text(str(csv_flag), style=csv_style))

    console.print()
    console.print(Panel(info_table, title=f"[title]{report_name}[/]", border_style="cyan", padding=(1, 2)))

    params = config.get("reportParameterMap", {}).get("reportParameter", [])
    if params:
        param_table = Table(
            title=f"Parametri ({len(params)})",
            title_style="title",
            border_style="dim cyan",
            header_style="bold white",
            show_lines=False,
            pad_edge=True,
            expand=True,
        )
        param_table.add_column("#", style="dim", width=4, justify="right")
        param_table.add_column("Nome", style="key", ratio=2)
        param_table.add_column("Filtro", style="value", ratio=2)
        param_table.add_column("Tipo", style="info", ratio=1)

        for i, p in enumerate(params, 1):
            param_table.add_row(str(i), p["name"], p["filtername"], p["paramtype"])

        console.print()
        console.print(param_table)

    console.print()
    return 0


def _show_results(df, args) -> int:
    if df.empty:
        console.print("\n[warning]⚠  Nessun dato trovato.[/]\n")
        return 1

    count = len(df)
    table = Table(
        title=f"Risultati — {count:,} record",
        title_style="title",
        border_style="dim cyan",
        header_style="bold white",
        show_lines=False,
        pad_edge=True,
        row_styles=["", "on grey7"],
    )

    for col in df.columns:
        justify = "right" if df[col].dtype.kind in ("i", "f") else "left"
        table.add_column(str(col), justify=justify, overflow="ellipsis", max_width=40)

    display_df = df.head(50)
    for _, row in display_df.iterrows():
        cells = []
        for col in df.columns:
            val = row[col]
            cell = str(val) if val is not None else "–"
            if col.lower() in ("status", "operationstatus"):
                if cell.lower() == "pass":
                    cell = f"[success]{cell}[/]"
                elif cell.lower() == "fail":
                    cell = f"[error]{cell}[/]"
                elif cell.lower() == "aborted":
                    cell = f"[warning]{cell}[/]"
            cells.append(cell)
        table.add_row(*cells)

    if count > 50:
        table.caption = f"[info]Mostrati 50 di {count:,} record[/]"

    console.print()
    console.print(table)

    if args.csv:
        df.to_csv(args.csv, index=False, encoding="utf-8-sig")
        console.print(f"\n  [success]✓[/]  Salvato in [key]{args.csv}[/]\n")
    else:
        console.print()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Proligent Analytics — Query con filtri personalizzati",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Esempi:\n"
            "  py main.py --station 92671\n"
            "  py main.py --station 92671 --date-from 2026-06-01 --status Pass\n"
            "  py main.py --station 92671 --csv output.csv\n"
            "  py main.py --list-reports\n"
        ),
    )

    auth = parser.add_argument_group("Autenticazione")
    auth.add_argument("--username", "-u", help="Email aziendale")
    auth.add_argument("--password", "-p", help="Password")
    auth.add_argument("--headless", action="store_true",
                      help="Browser invisibile")

    query = parser.add_argument_group("Query")
    query.add_argument("--report", "-r", default="OperationRuns",
                       help="Nome report (default: OperationRuns)")
    query.add_argument("--station", "-s", help="Chiave stazione (es. 92671)")
    query.add_argument("--date-from", help="Data inizio (es. 2026-06-01)")
    query.add_argument("--date-to", help="Data fine (es. 2026-06-30)")
    query.add_argument("--status", help="Filtro status (Pass, Fail, Aborted)")
    query.add_argument("--operation", help="Chiave operazione")
    query.add_argument("--product", help="Chiave prodotto")
    query.add_argument("--serial", help="Serial number")
    query.add_argument("--top", type=int, help="Numero max record")

    output = parser.add_argument_group("Output")
    output.add_argument("--csv", type=str, metavar="FILE",
                        help="Salva risultato in CSV")

    meta = parser.add_argument_group("Metadata")
    meta.add_argument("--list-reports", action="store_true",
                      help="Mostra tutti i report disponibili")
    meta.add_argument("--info", type=str, metavar="REPORT",
                      help="Mostra configurazione di un report")

    args = parser.parse_args()

    console.print(_banner())

    password = args.password
    if args.username and not password:
        password = getpass.getpass("Password: ")

    try:
        with console.status("[info]Login in corso…[/]"):
            client = ProligentClient()
            client.login(
                username=args.username,
                password=password,
                headless=args.headless,
            )
        console.print("  [success]✓[/]  Login effettuato\n")
    except RuntimeError as exc:
        console.print(f"\n[error]✗  Errore login:[/] {exc}\n")
        return 1

    if args.list_reports:
        return _show_reports(client)

    if args.info:
        return _show_info(client, args.info)

    filters = {
        "Report": args.report,
        "Stazione": args.station,
        "Da": args.date_from,
        "A": args.date_to,
        "Status": args.status,
        "Operazione": args.operation,
        "Prodotto": args.product,
        "Seriale": args.serial,
        "Limite": str(args.top) if args.top else None,
    }
    active = {k: v for k, v in filters.items() if v}
    if active:
        summary = "  ".join(f"[info]{k}:[/] [key]{v}[/]" for k, v in active.items())
        console.print(f"  {summary}\n")

    with console.status("[info]Esecuzione query…[/]"):
        df = client.query(
            args.report,
            station=args.station,
            date_from=args.date_from,
            date_to=args.date_to,
            status=args.status,
            operation=args.operation,
            product=args.product,
            serial=args.serial,
            top=args.top,
        )

    return _show_results(df, args)


if __name__ == "__main__":
    raise SystemExit(main())
