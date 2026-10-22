from dataclasses import dataclass
from typing import List, Optional
import os
import socket
import psutil

@dataclass
class PortEntry:
    port: int
    protocol: str
    pid: Optional[int]
    name: str
    status: str
    memory_mb: float
    command: str

def get_process_details(pid: Optional[int]):
    if not pid or pid == 0:
        return ("system", 0.0, "system")
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        try:
            mem = proc.memory_info().rss / (1024 * 1024)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            mem = 0.0
        try:
            cmdline = " ".join(proc.cmdline())
            if not cmdline:
                cmdline = name
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            cmdline = name
        return (name, round(mem, 1), cmdline)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ("unknown", 0.0, "unknown")

def scan_ports(target_port: Optional[int] = None, filter_text: Optional[str] = None) -> List[PortEntry]:
    entries = []
    seen = set()

    try:
        connections = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        return []

    for conn in connections:
        if conn.status not in (psutil.CONN_LISTEN, "LISTEN", psutil.CONN_NONE):
            if conn.type != socket.SOCK_DGRAM:
                continue

        if not conn.laddr:
            continue

        port = conn.laddr.port
        if target_port is not None and port != target_port:
            continue

        proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
        key = (port, proto, conn.pid)
        if key in seen:
            continue
        seen.add(key)

        name, mem, cmdline = get_process_details(conn.pid)

        if filter_text:
            text = filter_text.lower()
            port_match = text in str(port)
            name_match = text in name.lower()
            cmd_match = text in cmdline.lower()
            pid_match = text in str(conn.pid) if conn.pid else False
            if not (port_match or name_match or cmd_match or pid_match):
                continue

        entries.append(PortEntry(
            port=port,
            protocol=proto,
            pid=conn.pid,
            name=name,
            status=conn.status or "LISTEN",
            memory_mb=mem,
            command=cmdline[:80],
        ))

    entries.sort(key=lambda e: (e.port, e.protocol))
    return entries
