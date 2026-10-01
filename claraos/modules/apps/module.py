"""Compatibility shell that wires the App Hub into ClaraOS modules."""

import logging
from pathlib import Path

from ...application.apps import AppHubService
from ...core.module_base import BaseModule
from ...infrastructure.apps import DockerGateway, OmvComposeRegistry, YamlCatalogRepository
from ...presentation.api.apps_routes import build_apps_router

logger = logging.getLogger("claraos.modules.apps")


class AppsModule(BaseModule):
    name = "apps"
    title = "App Hub"
    description = "Compose-aware launcher and Store for NAS services"
    icon = "shapes"

    def __init__(self):
        super().__init__()
        resource_root = Path(__file__).resolve().parents[3] / "resources" / "app-catalog"
        service = AppHubService(
            catalog=YamlCatalogRepository(resource_root / "apps.yaml"),
            containers=DockerGateway(),
            registry=OmvComposeRegistry(),
        )
        self._router = build_apps_router(service)

    async def start(self) -> bool:
        self.is_running = True
        logger.info("AppsModule started")
        return True

    async def stop(self) -> bool:
        self.is_running = False
        logger.info("AppsModule stopped")
        return True
