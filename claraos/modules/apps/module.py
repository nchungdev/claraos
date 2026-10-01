"""Compose-aware application discovery for ClaraOS."""

import logging
import os
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import yaml

from fastapi import APIRouter, HTTPException

from ...core.module_base import BaseModule
from .catalog import APP_CATALOG
from .docker_client import docker_manager

logger = logging.getLogger("claraos.modules.apps")

# Infrastructure that supports ClaraOS itself is not an end-user app shortcut.
INTERNAL_CONTAINERS = {"claraos", "wildcard-gateway", "cloudflared-dashboard", "dashboard-web"}
OMV_CONFIG_PATH = os.getenv("OMV_CONFIG_PATH", "/host/etc/openmediavault/config.xml")


def _container_names(container: Dict[str, Any]) -> List[str]:
    return [name.lstrip("/").lower() for name in container.get("Names", [])]


def _compose_metadata(container: Dict[str, Any]) -> Dict[str, Optional[str]]:
    labels = container.get("Labels") or {}
    return {
        "compose_project": labels.get("com.docker.compose.project"),
        "compose_working_dir": labels.get("com.docker.compose.project.working_dir"),
        "compose_file": labels.get("com.docker.compose.project.config_files"),
    }


def _registered_omv_services(path: str = OMV_CONFIG_PATH) -> List[Dict[str, str]]:
    """Read OMV's Compose registry without granting ClaraOS write access to it."""
    if not os.path.isfile(path):
        return []
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError) as exc:
        logger.warning("Cannot read OMV Compose registry at %s: %s", path, exc)
        return []

    services: List[Dict[str, str]] = []
    for entry in root.findall("./services/compose/files/file"):
        file_uuid = entry.findtext("uuid", default="")
        file_name = entry.findtext("name", default="")
        body = entry.findtext("body", default="")
        try:
            definition = yaml.safe_load(body) or {}
        except yaml.YAMLError:
            logger.warning("Skipping invalid Compose YAML in OMV registry entry %s", file_name)
            continue
        for service_name, service in (definition.get("services") or {}).items():
            service = service if isinstance(service, dict) else {}
            services.append({
                "service_name": str(service_name),
                "container_name": str(service.get("container_name") or service_name),
                "compose_name": file_name,
                "compose_uuid": file_uuid,
            })
    return services


class AppsModule(BaseModule):
    name = "apps"
    title = "App Hub"
    description = "Compose-aware launcher for media, cloud and agent services"
    icon = "shapes"

    def __init__(self):
        super().__init__()
        self._router = APIRouter()
        self._setup_routes()

    @staticmethod
    def _find_container(app: Dict[str, Any], containers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        expected = {app["id"].lower(), app.get("container_name", "").lower()}
        expected.discard("")
        return next((item for item in containers if expected.intersection(_container_names(item))), None)

    def _setup_routes(self):
        @self._router.get("/catalog")
        async def get_catalog():
            containers = await docker_manager.list_containers(all_containers=True)
            registered = _registered_omv_services()
            registered_by_container = {item["container_name"].lower(): item for item in registered}
            catalog: List[Dict[str, Any]] = []
            claimed_names = set()

            # The five workflow services requested by the user always lead the hub.
            # A stopped service remains visible so the dashboard never hides intent.
            for app in APP_CATALOG:
                container = self._find_container(app, containers)
                expected_name = app.get("container_name", app["id"])
                claimed_names.add(expected_name.lower())
                if container:
                    claimed_names.update(_container_names(container))
                state = container.get("State", "not_installed") if container else "not_installed"
                compose = _compose_metadata(container) if container else {}
                registry = registered_by_container.get(expected_name.lower())
                if registry and not container:
                    state = "registered"
                catalog.append({
                    **app,
                    **compose,
                    "compose_name": registry.get("compose_name") if registry else compose.get("compose_project"),
                    "compose_uuid": registry.get("compose_uuid") if registry else None,
                    "source": "OMV Compose" if (registry or compose.get("compose_project")) else "Managed service",
                    "installed": container is not None or registry is not None,
                    "state": state,
                    "container_id": container.get("Id") if container else None,
                    "is_running": state == "running",
                })

            # CasaOS-like discovery: show every existing service, but keep the
            # Compose project as its owner instead of pretending ClaraOS owns it.
            for container in containers:
                names = _container_names(container)
                name = names[0] if names else container.get("Id", "unknown")[:12]
                if name in INTERNAL_CONTAINERS or any(item in claimed_names for item in names):
                    continue
                compose = _compose_metadata(container)
                state = container.get("State", "not_installed")
                catalog.append({
                    "id": f"discovered-{name}",
                    "name": name,
                    "category": "Đã phát hiện",
                    "description": f"{compose.get('compose_project') or 'Docker'} · {container.get('Image', 'unknown image')}",
                    "icon": "fa-cube",
                    "logo_id": name,
                    "container_name": name,
                    "installed": True,
                    "state": state,
                    "container_id": container.get("Id"),
                    "is_running": state == "running",
                    "manageable": False,
                    "protected": True,
                    "discovered": True,
                    "source": "OMV Compose" if compose.get("compose_project") else "Docker",
                    **compose,
                })

            # Include Compose definitions which OMV has registered but which do
            # not currently have a container (for example, a stopped stack).
            known = claimed_names | {name for container in containers for name in _container_names(container)}
            for service in registered:
                name = service["container_name"].lower()
                if name in INTERNAL_CONTAINERS or name in known:
                    continue
                catalog.append({
                    "id": f"omv-{service['compose_uuid']}-{service['service_name']}",
                    "name": service["service_name"],
                    "category": "Đã phát hiện",
                    "description": f"OMV Compose · {service['compose_name']} (chưa có container runtime)",
                    "icon": "fa-cube",
                    "logo_id": service["service_name"],
                    "container_name": service["container_name"],
                    "installed": True,
                    "state": "registered",
                    "container_id": None,
                    "is_running": False,
                    "manageable": False,
                    "protected": True,
                    "discovered": True,
                    "source": "OMV Compose",
                    "compose_name": service["compose_name"],
                    "compose_uuid": service["compose_uuid"],
                })

            return {
                "catalog": catalog,
                "docker_available": bool(containers) or bool(docker_manager._get_client()),
                "omv_compose_available": os.path.isfile(OMV_CONFIG_PATH),
            }

        @self._router.post("/{app_id}/{action}")
        async def app_action(app_id: str, action: str):
            # Avoid creating docker-run drift alongside an OMV Compose managed NAS.
            if action == "install":
                raise HTTPException(
                    status_code=409,
                    detail="Cài mới qua template OMV Compose để giữ volumes, secrets và update policy trong một nơi.",
                )
            raise HTTPException(status_code=405, detail="Quản lý vòng đời service này từ OMV Compose.")

    async def start(self) -> bool:
        self.is_running = True
        logger.info("AppsModule started")
        return True

    async def stop(self) -> bool:
        self.is_running = False
        logger.info("AppsModule stopped")
        return True
