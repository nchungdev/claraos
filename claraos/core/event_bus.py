import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine, Dict, List

logger = logging.getLogger("claraos.events")


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Coroutine]]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable[[Any], Coroutine]):
        """Subscribe an async coroutine handler to an event."""
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to event '{event_name}'")

    def unsubscribe(self, event_name: str, handler: Callable[[Any], Coroutine]):
        """Unsubscribe handler from an event."""
        if event_name in self._subscribers and handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)

    async def emit(self, event_name: str, data: Any = None):
        """Emit an event to all subscribers concurrently in background tasks."""
        handlers = self._subscribers.get(event_name, [])
        if not handlers:
            return

        logger.info(f"Event emitted: '{event_name}' (Dispatching to {len(handlers)} handlers)")
        tasks = []
        for handler in handlers:
            tasks.append(asyncio.create_task(self._safe_execute(handler, event_name, data)))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_execute(self, handler: Callable[[Any], Coroutine], event_name: str, data: Any):
        try:
            await handler(data)
        except Exception as e:
            logger.error(f"Error handling event '{event_name}' in {handler.__name__}: {e}", exc_info=True)


# Global singleton instance
event_bus = EventBus()
