"""Pure App Hub entities. They must not import Docker, OMV, or FastAPI."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class AppDefinition:
    id: str
    name: str
    description: str
    category: str
    container_name: str
    container_aliases: Tuple[str, ...] = ()
    icon: str = "fa-cube"
    logo_id: str = ""
    url: Optional[str] = None
    default_port: Optional[int] = None
    installable: bool = False
    image: Optional[str] = None
    template: Optional[str] = None
    logo: Optional[str] = None
    subdomain: Optional[str] = None


@dataclass(frozen=True)
class ComposeService:
    service_name: str
    container_name: str
    compose_name: str
    compose_uuid: str
