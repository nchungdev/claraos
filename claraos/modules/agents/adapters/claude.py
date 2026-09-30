import os
import shutil
import asyncio
from typing import Dict, Any, AsyncGenerator
from .base import BaseAgentAdapter


class ClaudeCodeAdapter(BaseAgentAdapter):
    engine_id = "claude"
    name = "Anthropic Claude Code"
    description = "Next-generation terminal coding assistant powered by Claude 3.7 Sonnet."

    async def is_available(self) -> bool:
        return shutil.which("claude") is not None

    async def get_quotas(self) -> Dict[str, Any]:
        return {
            "engine": "claude",
            "models": {
                "claude-3-7-sonnet": {"quota_pct": 95, "status": "healthy"}
            }
        }

    async def execute_prompt(self, prompt: str, workspace_path: str) -> AsyncGenerator[str, None]:
        yield f"⚡ [Claude Code] Processing prompt in '{workspace_path}'...\n"
        await asyncio.sleep(0.5)
        yield f"Running reasoning chain for: '{prompt}'\n"
