import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import httpx

from ...core.module_base import BaseModule
from ...core.config import config
from ...core.event_bus import event_bus

logger = logging.getLogger("claraos.modules.debrid")


class AddTorrentRequest(BaseModel):
    magnet_or_url: str
    seed: Optional[int] = 1


class DebridModule(BaseModule):
    name = "debrid"
    title = "Debrid Ingestion"
    description = "Cloud debrid cache downloader (Torbox/RealDebrid) & automated ingest bridge"
    icon = "arrow-down-tray"

    def __init__(self):
        super().__init__()
        self._router = APIRouter()
        self._setup_routes()
        self._worker_task: Optional[asyncio.Task] = None

    def _get_api_headers(self) -> Dict[str, str]:
        token = config.get("modules", "debrid", "api_key", default="")
        if not token:
            raise HTTPException(status_code=400, detail="Debrid API token is not configured")
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "ClaraOS-Debrid/1.0"
        }

    def _setup_routes(self):
        @self._router.get("/torrents")
        async def list_torrents():
            token = config.get("modules", "debrid", "api_key", default="")
            if not token:
                return {"torrents": [], "configured": False, "message": "API key required"}

            url = "https://api.torbox.app/v1/api/torrents/mylist"
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=self._get_api_headers(), timeout=15.0)
                if res.status_code != 200:
                    raise HTTPException(status_code=res.status_code, detail="Failed to fetch torrent list")
                data = res.json()
                return {"torrents": data.get("data", []), "configured": True}

        @self._router.post("/torrents")
        async def add_torrent(req: AddTorrentRequest):
            url = "https://api.torbox.app/v1/api/torrents/createtorrent"
            payload = {"magnet": req.magnet_or_url, "seed": req.seed}
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=self._get_api_headers(), data=payload, timeout=20.0)
                if res.status_code != 200:
                    raise HTTPException(status_code=res.status_code, detail="Failed to create torrent")
                return res.json()

    async def _poll_worker(self):
        logger.info("DebridModule background poller started")
        try:
            while self.is_running:
                interval = config.get("modules", "debrid", "poll_interval", default=30)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("DebridModule poller cancelled")

    async def start(self) -> bool:
        if self.is_running:
            return True
        self.is_running = True
        self._worker_task = asyncio.create_task(self._poll_worker())
        logger.info("DebridModule started")
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
        logger.info("DebridModule stopped")
        return True
