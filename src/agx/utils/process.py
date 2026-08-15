"""
Process Inspection & Management
==============================
"""

import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import List

from agx.config import IDE_EXECUTABLE, IS_MAC, IS_WINDOWS


def get_ide_pids() -> List[int]:
    my_pid = os.getpid()
    try:
        parent_pid = os.getppid()
    except Exception:
        parent_pid = -1

    pids = set()
    try:
        if IS_WINDOWS:
            for img in ["Antigravity IDE.exe", "Antigravity.exe", "antigravity-ide.exe"]:
                out = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {img}", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                )
                for line in out.stdout.splitlines():
                    parts = line.split(",")
                    if len(parts) >= 2 and any(k.lower() in parts[0].lower() for k in ["antigravity"]):
                        try:
                            pid = int(parts[1].strip('"'))
                            if pid not in (my_pid, parent_pid):
                                pids.add(pid)
                        except ValueError:
                            pass
        else:
            # Look for Antigravity electron / IDE processes specifically
            patterns = ["Antigravity IDE", "antigravity-ide"]
            for pat in patterns:
                out = subprocess.run(["pgrep", "-f", pat], capture_output=True, text=True)
                for p in out.stdout.split():
                    try:
                        pid = int(p.strip())
                        if pid not in (my_pid, parent_pid):
                            pids.add(pid)
                    except ValueError:
                        pass
    except Exception:
        pass

    return list(pids)


def is_ide_running() -> bool:
    return len(get_ide_pids()) > 0


def stop_ide(timeout_seconds: float = 8.0) -> bool:
    pids = get_ide_pids()
    if not pids:
        return True

    if IS_WINDOWS:
        try:
            for img in ["Antigravity IDE.exe", "Antigravity.exe", "antigravity-ide.exe"]:
                subprocess.run(["taskkill", "/F", "/IM", img], capture_output=True)
            return not is_ide_running()
        except Exception:
            return False

    for pid in pids:
        try:
            os.kill(pid, 15)  # SIGTERM
        except ProcessLookupError:
            pass

    steps = int(timeout_seconds * 2)
    for _ in range(steps):
        time.sleep(0.5)
        if not is_ide_running():
            return True

    for pid in get_ide_pids():
        try:
            os.kill(pid, 9)  # SIGKILL
        except ProcessLookupError:
            pass
    time.sleep(0.5)
    return not is_ide_running()


def start_ide() -> bool:
    try:
        exe = IDE_EXECUTABLE
        if not exe:
            return False

        if IS_WINDOWS:
            subprocess.Popen([exe], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            return True

        if IS_MAC:
            if exe.endswith(".app") or Path(exe).is_dir():
                subprocess.Popen(["open", "-a", exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            else:
                args = shlex.split(exe)
                subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            return True

        # Linux / Unix
        args = shlex.split(exe)
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except Exception:
        return False
