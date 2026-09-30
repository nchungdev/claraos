import asyncio
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.module_base import BaseModule
from .adapters.agy import AntigravityAdapter
from .adapters.claude import ClaudeCodeAdapter

logger = logging.getLogger("claraos.modules.agents")


class PromptRequest(BaseModel):
    engine: str = "antigravity"
    prompt: str
    workspace: str = "/home/chungnh/AI Workspace"


class AgentsModule(BaseModule):
    name = "agents"
    title = "Clara AI Agent Studio"
    description = "Universal Web GUI & Studio for Coding Agents (Google Antigravity, Claude Code & Codex)"
    icon = "robot"

    def __init__(self):
        super().__init__()
        self._router = APIRouter()
        self._adapters = {
            "antigravity": AntigravityAdapter(),
            "claude": ClaudeCodeAdapter()
        }
        self._setup_routes()

    def _setup_routes(self):
        @self._router.get("/engines")
        async def list_engines():
            results = []
            for engine_id, adapter in self._adapters.items():
                available = await adapter.is_available()
                results.append({
                    "id": engine_id,
                    "name": adapter.name,
                    "description": adapter.description,
                    "available": available
                })
            return {"engines": results}

        @self._router.get("/quotas")
        async def get_all_quotas():
            data = {}
            for engine_id, adapter in self._adapters.items():
                data[engine_id] = await adapter.get_quotas()
            return {"quotas": data}

        @self._router.post("/prompt")
        async def execute_prompt(req: PromptRequest):
            adapter = self._adapters.get(req.engine)
            if not adapter:
                raise HTTPException(status_code=404, detail="Agent engine not found")

            # Collect initial response chunks
            output = []
            async for chunk in adapter.execute_prompt(req.prompt, req.workspace):
                output.append(chunk)

            return {
                "status": "success",
                "engine": req.engine,
                "workspace": req.workspace,
                "output": "".join(output)
            }

    async def start(self) -> bool:
        self.is_running = True
        logger.info("AgentsModule started")
        return True

    async def stop(self) -> bool:
        self.is_running = False
        logger.info("AgentsModule stopped")
        return True
