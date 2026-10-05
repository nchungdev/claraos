import asyncio
import logging
import os
from typing import Dict, Any, List
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.module_base import BaseModule
from ...infrastructure.apps.omv_registry_reader import OmvComposeRegistry
from .catalog import APP_CATALOG, get_full_catalog, sync_community_catalog
from .docker_client import docker_manager

logger = logging.getLogger("claraos.modules.apps")


class AppsModule(BaseModule):
    name = "apps"
    title = "App Hub"
    description = "Compose-aware launcher and Store for NAS services"
    icon = "shapes"

    def __init__(self):
        super().__init__()
        self._router = APIRouter()
        self._omv_registry = OmvComposeRegistry()
        self._setup_routes()

    def _resolve_compose_uuids(self) -> Dict[str, str]:
        uuid_map = {}
        for s in self._omv_registry.list_services():
            uuid_map[s.service_name.lower()] = s.compose_uuid
            uuid_map[s.compose_name.lower().strip()] = s.compose_uuid
        return uuid_map

    def _setup_routes(self):
        @self._router.get("/catalog")
        @self._router.get("/store")
        async def get_catalog():
            containers = await docker_manager.list_containers(all_containers=True)
            container_map = {}
            for c in containers:
                names = [n.lstrip("/") for n in c.get("Names", [])]
                for n in names:
                    container_map[n.lower()] = c

            uuid_map = self._resolve_compose_uuids()
            catalog_with_status = []
            catalog_ids = set()

            full_catalog = get_full_catalog()
            for app in full_catalog:
                app_id = app["id"].lower()
                catalog_ids.add(app_id)
                compose_uuid = (
                    uuid_map.get(app_id)
                    or uuid_map.get(app.get("container_name", "").lower())
                    or ""
                )

                if app_id == "agy-manager":
                    continue

                if app_id in ("rclone", "media-organizer", "debrid-ingest", "omv", "agent-hub"):
                    catalog_with_status.append({
                        **app,
                        "restartable": bool(app.get("restart")),
                        "compose_uuid": compose_uuid,
                        "installed": True,
                        "state": "running",
                        "container_id": app.get("container_name", app_id),
                        "is_running": True
                    })
                    continue

                c = container_map.get(app_id)
                installed = c is not None
                state = c.get("State", "stopped") if c else "not_installed"
                cid = c.get("Id") if c else None
                img = app.get("image") or (c.get("Image") if c else "")
                
                catalog_with_status.append({
                    **app,
                    "compose_uuid": compose_uuid,
                    "image": img,
                    "restartable": installed,
                    "installed": installed,
                    "state": state,
                    "container_id": cid,
                    "is_running": state == "running"
                })

            # Auto-discover any active docker containers on NAS not in static catalog
            ignored_containers = {"claraos", "wildcard-gateway", "cloudflared-dashboard", "dashboard-web", "debrid-manager", "torbox-worker", "flaresolverr", "agy-manager", "rsshub-core"}
            for name, c in container_map.items():
                if name in catalog_ids or name in ignored_containers:
                    continue
                # Extract primary public port if available
                public_port = 80
                for p in c.get("Ports", []):
                    if isinstance(p, dict) and p.get("PublicPort"):
                        public_port = p["PublicPort"]
                        break

                catalog_with_status.append({
                    "id": name,
                    "name": name.capitalize(),
                    "category": "Docker",
                    "description": f"Container {name} on NAS ({c.get('Image', '')})",
                    "icon": "fa-cube",
                    "logo_id": name,
                    "image": c.get("Image", ""),
                    "default_port": public_port,
                    "installed": True,
                    "state": c.get("State", "running"),
                    "container_id": c.get("Id"),
                    "is_running": c.get("State") == "running",
                    "manageable": False,
                    "protected": True,
                    "restartable": True,
                    "compose_uuid": uuid_map.get(name.lower(), "")
                })

            return {
                "catalog": catalog_with_status,
                "docker_available": bool(containers) or bool(docker_manager._get_client())
            }

        @self._router.post("/catalog/sync")
        async def sync_catalog():
            count = await asyncio.to_thread(sync_community_catalog)
            return {"status": "ok", "synced_count": count}

        class InstallPayload(BaseModel):
            ports: Dict[str, str] = None
            volumes: List[str] = None
            wipe_existing_data: bool = False

        class UninstallPayload(BaseModel):
            purge_data: bool = False

        @self._router.get("/{app_id}/setup-schema")
        async def get_app_setup_schema(app_id: str):
            app = next((a for a in get_full_catalog() if a["id"].lower() == app_id.lower()), None)
            if not app:
                raise HTTPException(status_code=404, detail="App not found in catalog")

            # Check if previous data exists on host at /appdata/{app_id}
            has_existing_data = await docker_manager.check_app_config_exists(app["id"])
            return {
                "id": app["id"],
                "name": app["name"],
                "image": app.get("image", ""),
                "default_port": app.get("default_port"),
                "ports": app.get("ports", {}),
                "volumes": app.get("volumes", []),
                "env": app.get("env", []),
                "has_existing_data": has_existing_data,
                "config_path": f"/appdata/{app['id']}"
            }

        @self._router.post("/{app_id}/install")
        async def install_app(app_id: str, payload: InstallPayload = None):
            app = next((a for a in get_full_catalog() if a["id"].lower() == app_id.lower()), None)
            if not app:
                raise HTTPException(status_code=404, detail="App not found in catalog")
            if app.get("native"):
                return {"status": "success", "message": f"{app['name']} is a native ClaraOS service."}

            containers = await docker_manager.list_containers(all_containers=True)
            c = next((item for item in containers if any(n.lstrip("/").lower() == app_id.lower() for n in item.get("Names", []))), None)
            if c:
                raise HTTPException(status_code=400, detail="Container is already installed")

            # Determine ports & volumes
            target_ports = payload.ports if (payload and payload.ports is not None) else app.get("ports", {})
            target_volumes = payload.volumes if (payload and payload.volumes is not None) else app.get("volumes", [])
            wipe_existing = payload.wipe_existing_data if payload else False

            if wipe_existing:
                logger.info(f"Wiping existing config for '{app['id']}' before clean install...")
                await docker_manager.purge_app_config(app["id"])

            ok = await docker_manager.pull_and_run(
                image=app["image"],
                name=app["id"],
                ports=target_ports,
                volumes=target_volumes,
                env=app.get("env", [])
            )
            if not ok:
                raise HTTPException(status_code=500, detail="Failed to deploy container")
            return {"status": "ok", "action": "installed"}

        @self._router.post("/{app_id}/uninstall")
        async def uninstall_app(app_id: str, payload: UninstallPayload = None):
            app = next((a for a in get_full_catalog() if a["id"].lower() == app_id.lower()), None)
            if not app:
                raise HTTPException(status_code=404, detail="App not found in catalog")

            containers = await docker_manager.list_containers(all_containers=True)
            c = next((item for item in containers if any(n.lstrip("/").lower() == app_id.lower() for n in item.get("Names", []))), None)
            if not c:
                raise HTTPException(status_code=404, detail="Container is not installed on this server")

            cid = c["Id"]
            ok = await docker_manager.remove_container(cid)
            if not ok:
                raise HTTPException(status_code=500, detail="Failed to remove container")

            purged = False
            if payload and payload.purge_data:
                logger.info(f"User requested data purge for '{app_id}'")
                purged = await docker_manager.purge_app_config(app_id)

            return {"status": "ok", "app_id": app_id, "action": "uninstalled", "purged": purged}

        @self._router.post("/{app_id}/{action}")
        async def app_action(app_id: str, action: str):
            app = next((a for a in get_full_catalog() if a["id"].lower() == app_id.lower()), None)
            if not app:
                raise HTTPException(status_code=404, detail="App not found in catalog")

            if app.get("native"):
                return {"status": "success", "message": f"{app['name']} is a native ClaraOS service."}

            containers = await docker_manager.list_containers(all_containers=True)
            c = next((item for item in containers if any(n.lstrip("/").lower() == app_id.lower() for n in item.get("Names", []))), None)

            if action == "install":
                return await install_app(app_id, None)

            # apps whose server is not a Docker container declare how to restart it in the catalog
            if action == "restart" and app.get("restart"):
                await self._restart_via_spec(app)
                return {"status": "ok", "app_id": app_id, "action": action}

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
                return await uninstall_app(app_id, None)
            else:
                raise HTTPException(status_code=400, detail="Invalid action")

            if not ok:
                raise HTTPException(status_code=500, detail=f"Failed to {action} container")

            return {"status": "ok", "app_id": app_id, "action": action}

    async def _restart_via_spec(self, app: Dict[str, Any]) -> None:
        spec = app["restart"]
        if spec.get("kind") != "http":
            raise HTTPException(status_code=400, detail="Unsupported restart method")
        url = os.environ.get(spec.get("url_env", ""), "") or spec["url"]
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.post(url)
        except httpx.HTTPError as e:
            logger.error("Restart of %s failed: %s", app["id"], e)
            raise HTTPException(status_code=502, detail=f"Cannot reach {app['name']} server: {e}")
        if res.status_code >= 300:
            raise HTTPException(status_code=502, detail=f"{app['name']} refused restart (HTTP {res.status_code})")

    async def start(self) -> bool:
        self.is_running = True
        logger.info("AppsModule started")
        return True

    async def stop(self) -> bool:
        self.is_running = False
        logger.info("AppsModule stopped")
        return True
