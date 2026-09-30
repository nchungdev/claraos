from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator


class BaseAgentAdapter(ABC):
    engine_id: str = "base"
    name: str = "Base Agent"
    description: str = "Base AI Agent Engine"

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if CLI binary/service is installed and responsive."""
        pass

    @abstractmethod
    async def get_quotas(self) -> Dict[str, Any]:
        """Fetch remaining model tokens / quotas."""
        pass

    @abstractmethod
    async def execute_prompt(self, prompt: str, workspace_path: str) -> AsyncGenerator[str, None]:
        """Stream response output for a given prompt in a workspace."""
        pass
