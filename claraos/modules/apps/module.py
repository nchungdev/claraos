import asyncio
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.module_base import BaseModule
from .catalog import APP_CATALOG
from .docker_client import docker_manager

logger = logging.getLogger("claraos.modules.apps")


class AppsModule(BaseModule):
    name = "apps"
    title = "App Store & Containers"
    description = "Docker App Store & manager for Plex, *Arr stack, Komga & media tools"
    icon = "puzzle-piece"

    def __init__(self):
        super().__init__()
        self._router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        @self._router.get("/catalog")
        async def get_catalog():
            containers = await docker_manager.list_containers(all_containers=True)
            container_map = {}
            for c in containers:
                names = [n.lstrip("/") for n in c.get("Names", [])]
                for n in names:
                    container_map[n.lower()] = c

            catalog_with_status = []
            for app in APP_CATALOG:
                if app.get("native"):
                    catalog_with_status.append({
                        **app,
                        "installed": True,
                        "state": "running",
                        "container_id": None,
                        "is_running": True
                    })
                    continue

                app_id = app["id"].lower()
                c = container_map.get(app_id)
                installed = c is not None
                state = c.get("State", "stopped") if c else "not_installed"
                cid = c.get("Id") if c else None
                
                catalog_with_status.append({
                    **app,
                    "installed": installed,
                    "state": state,
                    "container_id": cid,
                    "is_running": state == "running"
                })

            return {
                "catalog": catalog_with_status,
                "docker_available": bool(containers) or bool(docker_manager._get_client())
            }

        @self._router.post("/{app_id}/{action}")
        async def app_action(app_id: str, action: str):
            app = next((a for a in APP_CATALOG if a["id"].lower() == app_id.lower()), None)
            if not app:
                raise HTTPException(status_code=404, detail="App not found in catalog")

            if app.get("native"):
                return {"status": "success", "message": f"{app['name']} is a native ClaraOS service."}

            containers = await docker_manager.list_containers(all_containers=True)
            c = next((item for item in containers if any(n.lstrip("/").lower() == app_id.lower() for n in item.get("Names", []))), None)

            if action == "install":
                if c:
                    raise HTTPException(status_code=400, detail="Container is already installed")
                ok = await docker_manager.pull_and_run(
                    image=app["image"],
                    name=app["id"],
                    ports=app["ports"],
                    volumes=app["volumes"],
                    env=app["env"]
                )
                if not ok:
                    raise HTTPException(status_code=500, detail="Failed to deploy container")
                return {"status": "ok", "action": "installed"}

            if not c:
                raise HTTPException(status_code=404, detail="Container is not installed on this server")

            cid = c["Id"]
            if action == "start":
                ok = await docker_manager.start_container(cid)
            elif action == "stop":
                ok = await docker_manager.stop_container(cid)
            elif action == "restart":
                ok = await docker_manager.restart_container(cid)
            elif action == "uninstall":
                ok = await docker_manager.remove_container(cid)
            else:
                raise HTTPException(status_code=400, detail="Invalid action")

            if not ok:
                raise HTTPException(status_code=500, detail=f"Failed to {action} container")

            return {"status": "ok", "app_id": app_id, "action": action}

    async def start(self) -> bool:
        self.is_running = True
        logger.info("AppsModule started")
        return True

    async def stop(self) -> bool:
        self.is_running = False
        logger.info("AppsModule stopped")
        return True
