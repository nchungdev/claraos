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
