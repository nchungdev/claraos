import os
import time
import psutil
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.config import config
from ..core.module_manager import module_manager

router = APIRouter(prefix="/api", tags=["System Core"])
START_TIME = time.time()


class ToggleModuleRequest(BaseModel):
    enabled: bool


@router.get("/system/status")
async def get_system_status():
    mem = psutil.virtual_memory()
    uptime_sec = int(time.time() - START_TIME)

    # Detect primary storage pool (/data or /srv/mergerfs/MainPool), fallback to root
    storage_path = "/"
    for path in ["/data", "/srv/mergerfs/MainPool", "/"]:
        if os.path.exists(path):
            storage_path = path
            break

    try:
        disk = psutil.disk_usage(storage_path)
    except Exception:
        disk = psutil.disk_usage("/")
        storage_path = "/"

    def format_size(bytes_val: int) -> str:
        tb = bytes_val / (1024**4)
        if tb >= 1.0:
            return f"{round(tb, 1)}TB"
        gb = bytes_val / (1024**3)
        return f"{round(gb, 1)}GB"

    # Multi-disk inspection across all NAS drives
    all_disks = []
    known_paths = [
        ("/config", "NVMe SSD (Hệ điều hành / OS)", "SSD", "nvme0n1"),
        ("/data", "MainPool (MergerFS Storage Pool)", "Pool", "mergerfs"),
        ("/srv/mergerfs/MainPool", "MainPool (MergerFS Storage Pool)", "Pool", "mergerfs"),
        ("/srv/dev-disk-by-uuid-98bd3ebc-514a-4108-ac09-155de8462a10", "Ổ HDD 4TB (WD Red)", "HDD", "sdc1"),
        ("/srv/dev-disk-by-uuid-da1b5c6f-9494-4728-9e88-97e3caebeb20", "Ổ HDD 1TB (Seagate)", "HDD", "sde"),
        ("/srv/dev-disk-by-uuid-6e0168a7-d077-4245-8cb7-2a2b0f812b8e", "Ổ HDD 1TB (HGST)", "HDD", "sda1"),
    ]

    seen_devices = set()
    for path, label, dtype, dev_id in known_paths:
        if os.path.exists(path) and dev_id not in seen_devices:
            try:
                u = os.statvfs(path)
                t = u.f_blocks * u.f_frsize
                if t == 0:
                    continue
                f = u.f_bavail * u.f_frsize
                used = t - f
                pct = round((used / t) * 100, 1)
                seen_devices.add(dev_id)

                all_disks.append({
                    "id": dev_id,
                    "name": label,
                    "type": dtype,
                    "path": path,
                    "total_human": format_size(t),
                    "used_human": format_size(used),
                    "free_human": format_size(f),
                    "total_gb": round(t / (1024**3), 1),
                    "used_gb": round(used / (1024**3), 1),
                    "free_gb": round(f / (1024**3), 1),
                    "percent": pct
                })
            except Exception:
                pass

    return {
        "status": "healthy",
        "uptime_seconds": uptime_sec,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent
        },
        "disk": {
            "path": storage_path,
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent,
            "total_human": format_size(disk.total),
            "used_human": format_size(disk.used),
            "free_human": format_size(disk.free)
        },
        "disks": all_disks,
        "modules": module_manager.list_modules()
    }


@router.get("/modules")
async def list_modules():
    return {"modules": module_manager.list_modules()}


@router.post("/modules/{name}/toggle")
async def toggle_module(name: str, req: ToggleModuleRequest):
    try:
        await module_manager.toggle_module(name, req.enabled)
        return {"status": "ok", "module": name, "enabled": req.enabled}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_settings():
    return config.data


@router.post("/settings")
async def update_settings(new_settings: Dict[str, Any]):
    config.data.update(new_settings)
    config.save()
    return {"status": "ok", "message": "Settings saved successfully"}
