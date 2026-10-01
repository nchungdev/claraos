"""Docker Engine adapter used only for runtime inspection."""

import os
from typing import Any, Dict, List, Optional

import httpx


class DockerGateway:
    def __init__(self, socket_path: str = os.getenv("DOCKER_SOCKET_PATH", "/var/run/docker.sock")):
        self.socket_path = socket_path

    def is_available(self) -> bool:
        return os.path.exists(self.socket_path)

    def _client(self) -> Optional[httpx.AsyncClient]:
        if not self.is_available():
            return None
        return httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(uds=self.socket_path),
            base_url="http://docker",
            timeout=30.0,
        )

    async def list_containers(self) -> List[Dict[str, Any]]:
        client = self._client()
        if not client:
            return []
        try:
            async with client:
                response = await client.get("/containers/json", params={"all": "true"})
                return response.json() if response.status_code == 200 else []
        except httpx.HTTPError:
            return []
