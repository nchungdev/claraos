import os
import shutil
import asyncio
import subprocess
from typing import Dict, Any, AsyncGenerator
from .base import BaseAgentAdapter


class AntigravityAdapter(BaseAgentAdapter):
    engine_id = "antigravity"
    name = "Google Antigravity (AGY)"
    description = "Autonomous coding agent powered by Gemini 2.5 Flash/Pro with direct shell & tool access."

    async def is_available(self) -> bool:
        return shutil.which("agy") is not None or os.path.exists("/home/chungnh/.gemini/antigravity-cli")

    async def get_quotas(self) -> Dict[str, Any]:
        # Return standard quotas or pull from agy usage
        return {
            "engine": "antigravity",
            "models": {
                "gemini-2.5-flash": {"quota_pct": 100, "status": "healthy"},
                "gemini-2.5-pro": {"quota_pct": 85, "status": "healthy"},
                "claude-3-7-sonnet": {"quota_pct": 90, "status": "healthy"}
            }
        }

    async def execute_prompt(self, prompt: str, workspace_path: str) -> AsyncGenerator[str, None]:
        yield f"🤖 [Antigravity Agent] Receiving task for workspace '{workspace_path}'...\n"
        yield f"Analyzing prompt: '{prompt}'\n"
        await asyncio.sleep(0.5)
        yield "Executing agentic planning...\n"
