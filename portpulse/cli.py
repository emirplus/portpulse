from typing import List, Optional
import json
import sys
import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .scanner import scan_ports
from .killer import kill_port
from .tui import run_tui

console = Console()

@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.pass_context
def main(ctx, version):
    if version:
        click.echo(f"portpulse v{__version__}")
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        if sys.stdin.isatty() and sys.stdout.isatty():
            run_tui()
        else:
            ctx.invoke(list_ports)

@main.command(name="list")
@click.option("--filter", "-f", "filter_text", help="Filter by port, name or PID")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_ports(filter_text: Optional[str] = None, as_json: bool = False):
    entries = scan_ports(filter_text=filter_text)
    if as_json:
        data = [e.__dict__ for e in entries]
        click.echo(json.dumps(data, indent=2))
        return

    table = Table(
        title=f"portpulse - active listeners ({len(entries)})",
        header_style="bold magenta",
        expand=True,
    )
    table.add_column("Port", style="bold yellow", justify="right")
    table.add_column("Proto", style="dim")
    table.add_column("PID", style="green", justify="right")
    table.add_column("Process", style="bold white")
    table.add_column("RAM (MB)", style="blue", justify="right")
    table.add_column("Command", style="dim white")

    for e in entries:
        table.add_row(
            str(e.port),
            e.protocol,
            str(e.pid or "-"),
            e.name,
            str(e.memory_mb),
            e.command,
        )

    console.print(table)

@main.command(name="find")
@click.argument("port", type=int)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def find_port(port: int, as_json: bool = False):
    entries = scan_ports(target_port=port)
    if as_json:
        click.echo(json.dumps([e.__dict__ for e in entries], indent=2))
        return

    if not entries:
        console.print(f"[yellow]No process listening on port {port}[/yellow]")
        sys.exit(1)

    for e in entries:
        console.print(f"[bold yellow]Port {e.port}[/bold yellow] ({e.protocol}) -> [bold green]{e.name}[/bold green] (PID {e.pid})")
        console.print(f"  Command: [dim]{e.command}[/dim]")
        console.print(f"  Memory : {e.memory_mb} MB")

@main.command(name="kill")
@click.argument("ports", nargs=-1, type=int, required=True)
@click.option("--force", "-f", is_flag=True, help="Force kill immediately (SIGKILL)")
@click.option("--tree", "-t", is_flag=True, default=True, help="Kill process tree (default: True)")
def kill_ports(ports: List[int], force: bool, tree: bool):
    failed = False
    for port in ports:
        success, msg = kill_port(port, force=force, tree=tree)
        if success:
            console.print(f"[bold green]✔[/bold green] {msg}")
        else:
            console.print(f"[bold red]✘[/bold red] {msg}")
            failed = True

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

