import logging
from typing import Dict, List, Optional
from fastapi import FastAPI
from .config import config
from .event_bus import event_bus
from .module_base import BaseModule

logger = logging.getLogger("aetherbox.modules")


class ModuleManager:
    def __init__(self, app: Optional[FastAPI] = None):
        self.app = app
        self._registry: Dict[str, BaseModule] = {}

    def register(self, module: BaseModule):
        """Register a module instance into the registry."""
        self._registry[module.name] = module
        logger.info(f"Registered module: [{module.name}] - {module.title}")
        
        # If an app instance is provided and module has router, include it with prefix
        if self.app and module.get_router():
            self.app.include_router(module.get_router(), prefix=f"/api/modules/{module.name}", tags=[module.title])

    def get_module(self, name: str) -> Optional[BaseModule]:
        return self._registry.get(name)

    def list_modules(self) -> List[Dict]:
        """List all registered modules with their active status and config."""
        result = []
        for name, mod in self._registry.items():
            cfg_enabled = config.get("modules", name, "enabled", default=True)
            status = mod.get_status()
            status["enabled"] = cfg_enabled
            result.append(status)
        return result

    async def start_all(self):
        """Start all enabled modules on startup."""
        for name, mod in self._registry.items():
            is_enabled = config.get("modules", name, "enabled", default=True)
            if is_enabled:
                logger.info(f"Starting enabled module: [{name}]...")
                try:
                    await mod.start()
                except Exception as e:
                    logger.error(f"Failed to start module [{name}]: {e}", exc_info=True)
            else:
                logger.info(f"Module [{name}] is disabled in configuration. Skipping.")

    async def stop_all(self):
        """Stop all running modules gracefully on shutdown."""
        for name, mod in self._registry.items():
            if mod.is_running:
                logger.info(f"Stopping module: [{name}]...")
                try:
                    await mod.stop()
                except Exception as e:
                    logger.error(f"Error stopping module [{name}]: {e}", exc_info=True)

    async def toggle_module(self, name: str, enable: bool) -> bool:
        """Dynamically enable or disable a module at runtime."""
        mod = self.get_module(name)
        if not mod:
            raise ValueError(f"Module '{name}' not found")

        config.set("modules", name, "enabled", value=enable)
        config.save()

        if enable and not mod.is_running:
            logger.info(f"Dynamically starting module: [{name}]")
            await mod.start()
        elif not enable and mod.is_running:
            logger.info(f"Dynamically stopping module: [{name}]")
            await mod.stop()

        await event_bus.emit("module.toggled", {"name": name, "enabled": enable, "running": mod.is_running})
        return True


# Global singleton instance
module_manager = ModuleManager()
