from typing import Optional, List
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live

from .scanner import scan_ports, PortEntry
from .killer import kill_process

console = Console()

def get_single_key() -> str:
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getch()
        if ch in (b"\x00", b"\xe0"):
            ch2 = msvcrt.getch()
            if ch2 == b"H":
                return "UP"
            if ch2 == b"P":
                return "DOWN"
            if ch2 == b"M":
                return "RIGHT"
            if ch2 == b"K":
                return "LEFT"
        if ch == b"\r":
            return "ENTER"
        if ch in (b"\x1b",):
            return "ESC"
        if ch == b"\x08":
            return "BACKSPACE"
        try:
            return ch.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    else:
        import tty
        import termios
        import select
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            rlist, _, _ = select.select([sys.stdin], [], [], 0.2)
            if not rlist:
                return ""
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if not rlist:
                    return "ESC"
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "A":
                        return "UP"
                    if ch3 == "B":
                        return "DOWN"
            if ch == "\r" or ch == "\n":
                return "ENTER"
            if ch == "\x7f":
                return "BACKSPACE"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def render_dashboard(entries: List[PortEntry], selected_idx: int, filter_str: str, message: str) -> Table:
    table = Table(
        title=f"portpulse - active listeners ({len(entries)} ports)",
        title_style="bold cyan",
        header_style="bold magenta",
        expand=True,
        show_lines=False,
    )
    table.add_column("Port", style="bold yellow", width=8, justify="right")
    table.add_column("Proto", style="dim", width=6)
    table.add_column("PID", style="green", width=9, justify="right")
    table.add_column("Process Name", style="bold white", width=18)
    table.add_column("RAM (MB)", style="blue", width=10, justify="right")
    table.add_column("Command / Path", style="dim white")

    if not entries:
        table.add_row("-", "-", "-", "no ports matching", "-", "-")
        return table

    for idx, e in enumerate(entries):
        is_selected = idx == selected_idx
        pointer = "> " if is_selected else "  "
        port_style = "bold white on dark_green" if is_selected else "bold yellow"
        row_style = "on grey23" if is_selected else ""

        table.add_row(
            f"{pointer}{e.port}",
            e.protocol,
            str(e.pid or "-"),
            e.name,
            str(e.memory_mb),
            e.command,
            style=row_style,
        )

    return table

def run_tui():
    selected_idx = 0
    filter_str = ""
    message = ""
    in_search = False

    console.clear()

    while True:
        entries = scan_ports(filter_text=filter_str)
        if not entries:
            selected_idx = 0
        else:
            selected_idx = max(0, min(selected_idx, len(entries) - 1))

        console.clear()
        
        status_line = Text()
        if in_search:
            status_line.append(f"FILTER: {filter_str}_", style="bold green on black")
            status_line.append(" (press ENTER to apply, ESC to clear)")
        else:
            status_line.append("KEYS: ", style="bold")
            status_line.append("[↑/↓ or j/k] Navigate  ", style="cyan")
            status_line.append("[x] Kill  ", style="red")
            status_line.append("[X] Kill Tree  ", style="bold red")
            status_line.append("[/] Filter  ", style="green")
            status_line.append("[r] Refresh  ", style="yellow")
            status_line.append("[q] Quit", style="white")

        console.print(status_line)
        if message:
            console.print(Panel(message, style="bold yellow"))
            message = ""

        table = render_dashboard(entries, selected_idx, filter_str, message)
        console.print(table)

        key = get_single_key()
        if not key:
            continue

        if in_search:
            if key == "ENTER" or key == "ESC":
                in_search = False
            elif key == "BACKSPACE":
                filter_str = filter_str[:-1]
            elif len(key) == 1 and key.isprintable():
                filter_str += key
            continue

        if key in ("q", "Q", "ESC"):
            break
        elif key in ("UP", "k"):
            if selected_idx > 0:
                selected_idx -= 1
        elif key in ("DOWN", "j"):
            if selected_idx < len(entries) - 1:
                selected_idx += 1
        elif key == "/":
            in_search = True
        elif key in ("r", "R"):
            message = "Refreshed."
        elif key in ("x", "X"):
            if entries and entries[selected_idx].pid:
                target = entries[selected_idx]
                force_tree = key == "X"
                success, msg = kill_process(target.pid, force=force_tree, tree=force_tree)
                message = msg
            else:
                message = "Cannot kill process (missing PID)"
