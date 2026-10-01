"""Interfaces consumed by application use cases."""

from typing import Any, Dict, List, Protocol

from .entities import AppDefinition, ComposeService


class CatalogRepository(Protocol):
    def list_apps(self) -> List[AppDefinition]: ...


class ContainerGateway(Protocol):
    async def list_containers(self) -> List[Dict[str, Any]]: ...

    def is_available(self) -> bool: ...


class ComposeRegistry(Protocol):
    def list_services(self) -> List[ComposeService]: ...

    def is_available(self) -> bool: ...
