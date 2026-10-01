"""Read-only adapter for the OMV Compose registry."""

import logging
import os
from pathlib import Path
from typing import List
from xml.etree import ElementTree

import yaml

from ...domain.apps.entities import ComposeService

logger = logging.getLogger("claraos.omv_compose")


class OmvComposeRegistry:
    def __init__(self, path: str = os.getenv("OMV_CONFIG_PATH", "/host/etc/openmediavault/config.xml")):
        self.path = Path(path)

    def is_available(self) -> bool:
        return self.path.is_file()

    def list_services(self) -> List[ComposeService]:
        if not self.is_available():
            return []
        try:
            root = ElementTree.parse(self.path).getroot()
        except (ElementTree.ParseError, OSError) as exc:
            logger.warning("Cannot read OMV Compose registry: %s", exc)
            return []

        services: List[ComposeService] = []
        for entry in root.findall("./services/compose/files/file"):
            file_uuid = entry.findtext("uuid", default="")
            file_name = entry.findtext("name", default="")
            try:
                definition = yaml.safe_load(entry.findtext("body", default="")) or {}
            except yaml.YAMLError:
                logger.warning("Skipping invalid Compose YAML: %s", file_name)
                continue
            for service_name, service in (definition.get("services") or {}).items():
                service = service if isinstance(service, dict) else {}
                services.append(ComposeService(
                    service_name=str(service_name),
                    container_name=str(service.get("container_name") or service_name),
                    compose_name=file_name,
                    compose_uuid=file_uuid,
                ))
        return services
