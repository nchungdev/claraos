import os
import re
import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import httpx

from ...core.module_base import BaseModule
from ...core.config import config

logger = logging.getLogger("aetherbox.modules.organizer")


class MatchRequest(BaseModel):
    file_path: str
    tmdb_id: int
    media_type: str  # "movie" or "tv"
    title: str
    year: Optional[str] = None
    season: Optional[int] = None
    episode: Optional[int] = None


class OrganizerModule(BaseModule):
    name = "organizer"
    title = "Media Organizer"
    description = "TMDb auto-enricher, staging inspector & Plex standard library organizer"
    icon = "film"

    def __init__(self):
        super().__init__()
        self._router = APIRouter()
        self._setup_routes()
        self._worker_task: Optional[asyncio.Task] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    def _setup_routes(self):
        @self._router.get("/files")
        async def list_files():
            staging_dir = Path(config.get("modules", "organizer", "staging_dir", default="/data/staging"))
            if not staging_dir.exists():
                return {"files": [], "staging_dir": str(staging_dir), "exists": False}

            files = []
            for root, _, filenames in os.walk(staging_dir):
                for f in filenames:
                    p = Path(root) / f
                    if p.suffix.lower() in (".mkv", ".mp4", ".avi", ".mov"):
                        size = p.stat().st_size
                        files.append({
                            "path": str(p),
                            "name": p.name,
                            "relative_path": str(p.relative_to(staging_dir)),
                            "size": size,
                            "size_human": f"{size / (1024*1024):.1f} MB" if size < 1024**3 else f"{size / (1024**3):.2f} GB"
                        })
            return {"files": files, "count": len(files), "staging_dir": str(staging_dir), "exists": True}

        @self._router.get("/tmdb/search")
        async def search_tmdb(query: str = Query(..., min_length=1), media_type: str = "multi"):
            api_key = config.get("modules", "organizer", "tmdb_api_key", default="")
            if not api_key:
                return {"results": [], "error": "TMDB_API_KEY is not configured in settings"}

            url = f"https://api.themoviedb.org/3/search/{media_type}"
            headers = {"Accept": "application/json"}
            params = {"query": query, "language": config.get("modules", "organizer", "language", default="vi-VN")}
            if len(api_key) <= 32:
                params["api_key"] = api_key
            else:
                headers["Authorization"] = f"Bearer {api_key}"
            
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=headers, params=params, timeout=10.0)
                if res.status_code != 200:
                    raise HTTPException(status_code=res.status_code, detail="TMDb API query failed")
                data = res.json()
                return {"results": data.get("results", [])}

        @self._router.post("/organize")
        async def organize_file(req: MatchRequest):
            staging_file = Path(req.file_path)
            if not staging_file.exists():
                raise HTTPException(status_code=404, detail="Source file not found")

            # Clean name according to Plex standard
            ext = staging_file.suffix
            year_str = f" ({req.year})" if req.year else ""
            clean_title = re.sub(r'[\\/*?:"<>|]', "", req.title)

            if req.media_type == "movie":
                target_dir = Path(config.get("modules", "organizer", "movies_dir", default="/data/media/Movies")) / f"{clean_title}{year_str}"
                target_file = target_dir / f"{clean_title}{year_str}{ext}"
            else:
                s_num = req.season or 1
                e_num = req.episode or 1
                target_dir = Path(config.get("modules", "organizer", "tv_dir", default="/data/media/TV Shows")) / f"{clean_title}{year_str}" / f"Season {s_num:02d}"
                target_file = target_dir / f"{clean_title} - S{s_num:02d}E{e_num:02d}{ext}"

            target_dir.mkdir(parents=True, exist_ok=True)
            # Perform atomic move / hardlink
            try:
                os.link(staging_file, target_file)
                staging_file.unlink()
            except OSError:
                # Fallback to copy/move across devices
                import shutil
                shutil.move(str(staging_file), str(target_file))

            return {
                "status": "success",
                "source": str(staging_file),
                "destination": str(target_file),
                "title": req.title
            }

    async def start(self) -> bool:
        if self.is_running:
            return True
        self.is_running = True
        logger.info("OrganizerModule successfully started")
        return True

    async def stop(self) -> bool:
        if not self.is_running:
            return True
        self.is_running = False
        logger.info("OrganizerModule stopped")
        return True
