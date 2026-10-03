"""Loads versioned Store metadata from a repository resource file."""

from pathlib import Path
from typing import Any, Dict, List

import yaml

from ...domain.apps.entities import AppDefinition


class YamlCatalogRepository:
    def __init__(self, path: Path):
        self.path = path

    def list_apps(self) -> List[AppDefinition]:
        if not self.path.is_file():
            return []
        with self.path.open(encoding="utf-8") as source:
            raw = yaml.safe_load(source) or {}
        return [self._definition(item) for item in raw.get("apps", [])]

    @staticmethod
    def _definition(item: Dict[str, Any]) -> AppDefinition:
        return AppDefinition(
            id=item["id"],
            name=item["name"],
            description=item.get("description", ""),
            category=item.get("category", "Utilities"),
            container_name=item.get("container_name", item["id"]),
            container_aliases=tuple(item.get("container_aliases", [])),
            icon=item.get("icon", "fa-cube"),
            logo_id=item.get("logo_id", item["id"]),
            url=item.get("url"),
            default_port=item.get("default_port"),
            installable=bool(item.get("installable", False)),
            image=item.get("image"),
            template=item.get("template"),
            logo=item.get("logo"),
            subdomain=item.get("subdomain"),
        )
