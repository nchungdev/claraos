import asyncio
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from ...core.module_base import BaseModule
from ...core.config import config
from .rclone_manager import get_all_rclone_tasks, control_task, format_speed

logger = logging.getLogger("aetherbox.modules.sync")


class SyncModule(BaseModule):
    name = "sync"
    title = "Cloud Sync Pro"
    description = "Real-time Rclone process telemetry, SIGSTOP/CONT throttling & VFS monitor"
    icon: str = "cloud-arrow-up"

    def __init__(self):
        super().__init__()
        self._router = APIRouter()
        self._setup_routes()
        self._worker_task: asyncio.Task = None
        self._last_stats = {"total_speed_bps": 0, "tasks": []}

    def _setup_routes(self):
        @self._router.get("/stats")
        async def get_stats():
            tasks = get_all_rclone_tasks()
            total_speed = sum(t.get("speed_bps", 0) for t in tasks if t.get("category") == "transfer")
            return {
                "running": self.is_running,
                "total_speed_bps": total_speed,
                "total_speed_human": format_speed(total_speed),
                "tasks_count": len(tasks),
                "transfers": [t for t in tasks if t.get("category") == "transfer"],
                "mounts": [t for t in tasks if t.get("category") == "mount"],
                "all_tasks": tasks
            }

        @self._router.post("/tasks/{pid}/{action}")
        async def task_action(pid: int, action: str):
            if action not in ("pause", "resume", "stop"):
                raise HTTPException(status_code=400, detail="Invalid action")
            ok = control_task(pid, action)
            if not ok:
                raise HTTPException(status_code=500, detail=f"Failed to execute {action} on PID {pid}")
            return {"status": "ok", "pid": pid, "action": action}

    async def _monitor_loop(self):
        logger.info("SyncModule monitor loop started")
        try:
            while self.is_running:
                # Periodic scan
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            logger.info("SyncModule monitor loop cancelled")

    async def start(self) -> bool:
        if self.is_running:
            return True
        self.is_running = True
        self._worker_task = asyncio.create_task(self._monitor_loop())
        logger.info("SyncModule successfully started")
        return True

    async def stop(self) -> bool:
        if not self.is_running:
            return True
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("SyncModule stopped")
        return True

    def get_status(self) -> Dict[str, Any]:
        base = super().get_status()
        tasks = get_all_rclone_tasks()
        total_speed = sum(t.get("speed_bps", 0) for t in tasks if t.get("category") == "transfer")
        base.update({
            "active_tasks": len(tasks),
            "upload_speed": format_speed(total_speed)
        })
        return base
