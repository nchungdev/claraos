from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from fastapi import APIRouter


class BaseModule(ABC):
    name: str = "base"
    title: str = "Base Module"
    description: str = "Base module template"
    icon: str = "cube"

    def __init__(self):
        self.is_running: bool = False
        self._router: Optional[APIRouter] = None

    @abstractmethod
    async def start(self) -> bool:
        """Start module background tasks, timers, or listeners. Return True if successful."""
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """Gracefully stop module background tasks and release resources."""
        pass

    def get_router(self) -> Optional[APIRouter]:
        """Return FastAPI APIRouter instance if this module provides custom HTTP endpoints."""
        return self._router

    def get_status(self) -> Dict[str, Any]:
        """Return real-time diagnostic status of the module for the UI dashboard."""
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "icon": self.icon,
            "is_running": self.is_running
        }
