"""App Hub use cases: combine catalog intent with observed NAS state."""

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from ...domain.apps.entities import AppDefinition, ComposeService
from ...domain.apps.ports import CatalogRepository, ComposeRegistry, ContainerGateway

INTERNAL_CONTAINERS = {"claraos", "wildcard-gateway", "cloudflared-dashboard", "dashboard-web", "agy-manager"}
DISPLAY_NAMES = {
    "calibre-web": "Calibre Web", "filebrowser": "FileBrowser", "flaresolverr": "FlareSolverr",
    "jellyseerr": "Jellyseerr", "metube": "MeTube", "openlist": "OpenList",
    "ariang": "AriaNg",
}


def _container_names(container: Dict[str, Any]) -> List[str]:
    return [name.lstrip("/").lower() for name in container.get("Names", [])]


def _compose_metadata(container: Dict[str, Any]) -> Dict[str, Optional[str]]:
    labels = container.get("Labels") or {}
    return {
        "compose_project": labels.get("com.docker.compose.project"),
        "compose_working_dir": labels.get("com.docker.compose.project.working_dir"),
        "compose_file": labels.get("com.docker.compose.project.config_files"),
    }


def _display_name(value: str) -> str:
    return DISPLAY_NAMES.get(value.lower(), value.replace("-", " ").replace("_", " ").title())


class AppHubService:
    def __init__(self, catalog: CatalogRepository, containers: ContainerGateway, registry: ComposeRegistry):
        self.catalog = catalog
        self.containers = containers
        self.registry = registry

    async def list_installed_apps(self) -> Dict[str, Any]:
        containers = await self.containers.list_containers()
        registry = self.registry.list_services()
        definitions = self.catalog.list_apps()
        registry_by_container = {service.container_name.lower(): service for service in registry}
        catalog: List[Dict[str, Any]] = []
        claimed = set()

        # Catalog entries surface only after their Compose service exists.  Store
        # templates are optional; no app is forced into the App Hub on first run.
        for definition in definitions:
            container = self._find_container(definition, containers)
            service = next((registry_by_container.get(name) for name in self._candidate_names(definition) if registry_by_container.get(name)), None)
            if not container and not service:
                continue
            claimed.update(self._candidate_names(definition))
            if container:
                claimed.update(_container_names(container))
            catalog.append(self._catalog_record(definition, container, service))

        # Docker reports current runtime, including unmanaged containers. Display
        # them but preserve the Compose project when Docker provides labels.
        for container in containers:
            names = _container_names(container)
            name = names[0] if names else container.get("Id", "unknown")[:12]
            if name in INTERNAL_CONTAINERS or any(item in claimed for item in names):
                continue
            compose = _compose_metadata(container)
            state = container.get("State", "not_installed")
            catalog.append({
                "id": f"discovered-{name}", "name": _display_name(name), "category": "Đã phát hiện",
                "description": f"{compose.get('compose_project') or 'Docker'} · {container.get('Image', 'unknown image')}",
                "icon": "fa-cube", "logo_id": name, "container_name": name,
                "installed": True, "state": state, "container_id": container.get("Id"),
                "is_running": state == "running", "manageable": False, "protected": True,
                "discovered": True, "source": "OMV Compose" if compose.get("compose_project") else "Docker",
                **compose,
            })

        known = claimed | {name for container in containers for name in _container_names(container)}
        for service in registry:
            name = service.container_name.lower()
            if name in INTERNAL_CONTAINERS or name in known:
                continue
            catalog.append({
                "id": f"omv-{service.compose_uuid}-{service.service_name}",
                "name": _display_name(service.service_name), "category": "Đã phát hiện",
                "description": f"OMV Compose · {service.compose_name} (chưa có container runtime)",
                "icon": "fa-cube", "logo_id": service.service_name, "container_name": service.container_name,
                "installed": True, "state": "registered", "container_id": None, "is_running": False,
                "manageable": False, "protected": True, "discovered": True, "source": "OMV Compose",
                "compose_name": service.compose_name, "compose_uuid": service.compose_uuid,
            })

        return {
            "catalog": catalog,
            "docker_available": self.containers.is_available(),
            "omv_compose_available": self.registry.is_available(),
        }

    async def list_store_apps(self) -> Dict[str, Any]:
        """Optional templates only; availability does not imply installation."""
        containers = await self.containers.list_containers()
        registry = {item.container_name.lower() for item in self.registry.list_services()}
        records = []
        for definition in self.catalog.list_apps():
            if not definition.installable:
                continue
            container = self._find_container(definition, containers)
            state = container.get("State", "registered") if container else "registered" if registry.intersection(self._candidate_names(definition)) else "available"
            records.append({
                **asdict(definition), "installed": state != "available", "is_running": state == "running", "state": state,
            })
        return {"catalog": records}

    @staticmethod
    def _find_container(definition: AppDefinition, containers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        expected = AppHubService._candidate_names(definition)
        return next((item for item in containers if expected.intersection(_container_names(item))), None)

    @staticmethod
    def _candidate_names(definition: AppDefinition) -> set[str]:
        return {definition.id.lower(), definition.container_name.lower(), *(name.lower() for name in definition.container_aliases)}

    @staticmethod
    def _catalog_record(definition: AppDefinition, container: Optional[Dict[str, Any]], service: Optional[ComposeService]) -> Dict[str, Any]:
        state = container.get("State", "registered") if container else "registered"
        compose = _compose_metadata(container) if container else {}
        return {
            **asdict(definition), **compose,
            "compose_name": service.compose_name if service else compose.get("compose_project"),
            "compose_uuid": service.compose_uuid if service else None,
            "source": "OMV Compose", "installed": True, "state": state,
            "container_id": container.get("Id") if container else None, "is_running": state == "running",
            "manageable": False, "protected": True,
        }
