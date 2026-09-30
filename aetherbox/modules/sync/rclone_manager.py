#!/usr/bin/env python3
"""
System-wide Rclone Operations & Concurrency Manager for AetherBox.
Scans and controls all Rclone processes (DriveSync, Mounts, CLI).
"""

import os, glob, time, json, signal, subprocess, urllib.request, urllib.parse, re
from typing import Dict, List, Any, Optional

IO_CACHE = {}

def format_bytes(b):
    if b is None or b < 0:
        return "--"
    if b < 1024:
        return f"{b} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    elif b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):.2f} MB"
    else:
        return f"{b / (1024 * 1024 * 1024):.2f} GB"

def format_speed(bps):
    if bps is None or bps < 0:
        return "0.00 MB/s"
    if bps < 1024:
        return f"{bps:.0f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps / 1024:.1f} KB/s"
    elif bps < 1024 * 1024 * 1024:
        return f"{bps / (1024 * 1024):.2f} MB/s"
    else:
        return f"{bps / (1024 * 1024 * 1024):.2f} GB/s"

def format_eta(seconds):
    if seconds is None or seconds <= 0 or seconds > 86400 * 7:
        return "--:--"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def get_process_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            raw = f.read().decode("utf-8", errors="ignore").split("\0")
        return [x for x in raw if x]
    except Exception:
        return []

def get_process_stats(pid):
    mem_mb = 0.0
    state = "S"
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("State:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        state = parts[1]
                elif line.startswith("VmRSS:"):
                    val = line.split()[1]
                    mem_mb = round(int(val) / 1024, 1)
    except Exception:
        pass
    return state, mem_mb

def read_process_io(pid):
    rchar, wchar = 0, 0
    content = ""
    try:
        with open(f"/proc/{pid}/io") as f:
            content = f.read()
    except (PermissionError, FileNotFoundError):
        try:
            out = subprocess.run(["sudo", "cat", f"/proc/{pid}/io"], capture_output=True, text=True, timeout=1)
            content = out.stdout
        except Exception:
            pass

    for line in content.splitlines():
        if line.startswith("rchar:"):
            try: rchar = int(line.split()[1])
            except Exception: pass
        elif line.startswith("wchar:"):
            try: wchar = int(line.split()[1])
            except Exception: pass
    return rchar, wchar

def get_all_rclone_tasks() -> List[Dict[str, Any]]:
    tasks = []
    pids = []
    for p in glob.glob("/proc/[0-9]*"):
        try:
            pids.append(int(os.path.basename(p)))
        except ValueError:
            pass

    now = time.time()
    for pid in sorted(pids):
        cmd = get_process_cmdline(pid)
        if not cmd:
            continue
        bin_name = os.path.basename(cmd[0])
        if "rclone" not in bin_name:
            continue

        cmd_str = " ".join(cmd)
        state_code, mem_mb = get_process_stats(pid)
        rchar, wchar = read_process_io(pid)

        # Delta speed calculation
        speed_bps = 0
        if pid in IO_CACHE:
            last_t, last_r = IO_CACHE[pid]
            dt = now - last_t
            if dt > 0.4 and rchar >= last_r:
                speed_bps = (rchar - last_r) / dt
        IO_CACHE[pid] = (now, rchar)

        # Classify task
        is_mount = "mount" in cmd
        is_copy = "copy" in cmd or "move" in cmd or "sync" in cmd

        category = "other"
        display_name = "Rclone Task"
        if is_mount:
            category = "mount"
            display_name = f"VFS Mount (PID {pid})"
        elif is_copy:
            category = "transfer"
            # Extract src/dst
            for arg in cmd:
                if "Phim" in arg or "/media" in arg or "gdrive" in arg:
                    display_name = os.path.basename(arg.rstrip("/"))
                    break

        tasks.append({
            "pid": pid,
            "name": display_name,
            "category": category,
            "cmd": cmd_str,
            "state": "paused" if state_code == "T" else "running",
            "memory_mb": mem_mb,
            "speed_bps": speed_bps,
            "speed_human": format_speed(speed_bps),
            "bytes_read": rchar,
            "bytes_read_human": format_bytes(rchar)
        })

    return tasks

def control_task(pid: int, action: str) -> bool:
    try:
        if action == "pause":
            os.kill(pid, signal.SIGSTOP)
        elif action == "resume":
            os.kill(pid, signal.SIGCONT)
        elif action == "stop":
            os.kill(pid, signal.SIGTERM)
        return True
    except Exception as e:
        try:
            # Fallback to sudo if needed
            sig_map = {"pause": "-STOP", "resume": "-CONT", "stop": "-TERM"}
            if action in sig_map:
                subprocess.run(["sudo", "kill", sig_map[action], str(pid)], check=True)
                return True
        except Exception:
            pass
        return False
