from typing import Tuple, List
import os
import signal
import psutil

def kill_process(pid: int, force: bool = False, tree: bool = False) -> Tuple[bool, str]:
    if not pid or pid == 0:
        return (False, "Cannot kill system process (PID 0)")

    if pid == os.getpid():
        return (False, "Cannot kill portpulse itself")

    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return (False, f"Process {pid} does not exist")
    except psutil.AccessDenied:
        return (False, f"Permission denied for PID {pid}")

    procs_to_kill: List[psutil.Process] = []
    if tree:
        try:
            procs_to_kill = parent.children(recursive=True)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            procs_to_kill = []
    procs_to_kill.append(parent)

    killed_count = 0
    for proc in procs_to_kill:
        try:
            if force:
                proc.kill()
            else:
                proc.terminate()
            killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    gone, alive = psutil.wait_procs(procs_to_kill, timeout=2.0)
    for p in alive:
        try:
            p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return (True, f"Killed {killed_count} process(es) for PID {pid}")

def kill_port(port: int, force: bool = False, tree: bool = False) -> Tuple[bool, str]:
    from .scanner import scan_ports
    entries = [e for e in scan_ports(target_port=port) if e.pid]

    if not entries:
        return (False, f"No active process found listening on port {port}")

    killed = []
    errors = []
    pids = {e.pid for e in entries if e.pid}

    for pid in pids:
        success, msg = kill_process(pid, force=force, tree=tree)
        if success:
            killed.append(pid)
        else:
            errors.append(msg)

    if killed:
        return (True, f"Freed port {port} (killed PID {', '.join(str(p) for p in killed)})")
    return (False, f"Failed to free port {port}: {'; '.join(errors)}")
