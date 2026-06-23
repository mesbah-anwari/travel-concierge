"""CLI entrypoint:

    python -m travel_concierge "Plan a 5-day trip to Lisbon in mid-July for a couple, mid-range budget, food + history focus, home currency EUR"

If no argument is passed, you get an interactive prompt.
"""
from __future__ import annotations

import sys


def _missing_deps_message(exc: ImportError) -> str:
    return (
        "❌ Missing dependency: "
        f"{exc.name or exc.msg}\n\n"
        "It looks like you're running the system Python without the project\n"
        "dependencies installed. Two ways to fix this:\n\n"
        "  Option A (recommended) — use the project's virtual environment:\n"
        "      .\\.venv\\Scripts\\python.exe main.py \"<your trip request>\"\n"
        "    or activate it once per shell:\n"
        "      .\\.venv\\Scripts\\Activate.ps1\n"
        "      python main.py \"<your trip request>\"\n\n"
        "  Option B — install deps into your current Python:\n"
        "      python -m pip install -r requirements.txt\n"
    )


try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel

    from travel_concierge.runner import plan_trip
except ImportError as exc:  # pragma: no cover - friendly bootstrap message
    sys.stderr.write(_missing_deps_message(exc))
    raise SystemExit(1) from exc


console = Console()


def _read_request_from_argv_or_stdin() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    console.print(
        Panel.fit(
            "[bold cyan]Travel Concierge[/bold cyan]\n"
            "Describe your trip in one message. Include destination, dates "
            "(or duration), travellers, style and interests.\n"
            "[dim]Example: Plan a 5-day trip to Lisbon in July for a couple, "
            "mid-range, food + history, home currency EUR.[/dim]",
            border_style="cyan",
        )
    )
    return console.input("[bold]> [/bold]").strip()


def main() -> int:
    request = _read_request_from_argv_or_stdin()
    if not request:
        console.print("[yellow]No request provided. Exiting.[/yellow]")
        return 1
    with console.status("[cyan]Planning your trip…[/cyan]", spinner="dots"):
        try:
            answer = plan_trip(request)
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Error:[/red] {exc}")
            return 2
    console.print(Markdown(answer))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
