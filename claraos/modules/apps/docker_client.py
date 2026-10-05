import os
import logging
from typing import Dict, List, Any, Optional
import httpx

logger = logging.getLogger("claraos.docker")
DOCKER_SOCKET = os.getenv("DOCKER_SOCKET_PATH", "/var/run/docker.sock")


class DockerManager:
    def __init__(self, socket_path: str = DOCKER_SOCKET):
        self.socket_path = socket_path
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> Optional[httpx.AsyncClient]:
        if not os.path.exists(self.socket_path):
            return None
        if self._client is None or self._client.is_closed:
            transport = httpx.AsyncHTTPTransport(uds=self.socket_path)
            self._client = httpx.AsyncClient(transport=transport, base_url="http://docker", timeout=30.0)
        return self._client

    async def aclose(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            return []
        try:
            res = await client.get("/containers/json", params={"all": str(all_containers).lower()})
            if res.status_code == 200:
                return res.json()
            return []
        except Exception as e:
            logger.error(f"Error querying docker containers: {e}")
            return []

    async def start_container(self, container_id: str) -> bool:
        client = self._get_client()
        if not client: return False
        try:
            res = await client.post(f"/containers/{container_id}/start")
            return res.status_code in (204, 304)
        except Exception as e:
            logger.error(f"Error starting container {container_id}: {e}")
            return False

    async def stop_container(self, container_id: str) -> bool:
        client = self._get_client()
        if not client: return False
        try:
            res = await client.post(f"/containers/{container_id}/stop")
            return res.status_code in (204, 304)
        except Exception as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            return False

    async def restart_container(self, container_id: str) -> bool:
        client = self._get_client()
        if not client: return False
        try:
            res = await client.post(f"/containers/{container_id}/restart")
            return res.status_code in (204, 304)
        except Exception as e:
            logger.error(f"Error restarting container {container_id}: {e}")
            return False

    async def remove_container(self, container_id: str) -> bool:
        client = self._get_client()
        if not client: return False
        try:
            # Force remove container (stops and deletes container instance)
            res = await client.delete(f"/containers/{container_id}", params={"force": "true"})
            return res.status_code in (204, 200)
        except Exception as e:
            logger.error(f"Error removing container {container_id}: {e}")
            return False

    async def pull_and_run(self, image: str, name: str, ports: Dict[str, str], volumes: List[str], env: List[str]) -> bool:
        client = self._get_client()
        if not client: return False
        try:
            # 1. Pull image
            logger.info(f"Pulling image {image}...")
            pull_res = await client.post("/images/create", params={"fromImage": image}, timeout=180.0)
            if pull_res.status_code != 200:
                logger.error(f"Failed to pull image {image}: {pull_res.text}")
                return False

            # 2. Prepare container config
            exposed_ports = {}
            port_bindings = {}
            for host_port, container_port in ports.items():
                c_spec = f"{container_port}/tcp"
                exposed_ports[c_spec] = {}
                port_bindings[c_spec] = [{"HostPort": str(host_port)}]

            create_payload = {
                "Image": image,
                "Env": env,
                "ExposedPorts": exposed_ports,
                "HostConfig": {
                    "PortBindings": port_bindings,
                    "Binds": volumes,
                    "RestartPolicy": {"Name": "unless-stopped"}
                }
            }

            # 3. Create container
            create_res = await client.post("/containers/create", params={"name": name}, json=create_payload)
            if create_res.status_code not in (201, 200):
                logger.error(f"Failed to create container {name}: {create_res.text}")
                return False
            cid = create_res.json().get("Id")
            # 4. Start container
            start_res = await client.post(f"/containers/{cid}/start")
            return start_res.status_code in (204, 304)
        except Exception as e:
            logger.error(f"Error deploying container {name}: {e}")
            return False

    async def check_app_config_exists(self, app_id: str) -> bool:
        """Checks if /appdata/{app_id} exists on the host filesystem via a quick container inspect or test."""
        clean_id = app_id.strip().lower()
        if not clean_id:
            return False
        client = self._get_client()
        if not client:
            return False
        try:
            # We mount /appdata as read-only and test if child directory clean_id exists
            payload = {
                "Image": "ghcr.io/nchungdev/claraos:latest",
                "Cmd": ["sh", "-c", f'test -d "/parent/{clean_id}"'],
                "HostConfig": {
                    "Binds": ["/appdata:/parent:ro"]
                }
            }
            res = await client.post("/containers/create", json=payload)
            if res.status_code != 201:
                return False
            cid = res.json().get("Id")
            try:
                await client.post(f"/containers/{cid}/start")
                wait_res = await client.post(f"/containers/{cid}/wait")
                return wait_res.json().get("StatusCode") == 0
            finally:
                await client.delete(f"/containers/{cid}", params={"force": "true"})
        except Exception as e:
            logger.error(f"Error checking config existence for {clean_id}: {e}")
            return False

    async def purge_app_config(self, app_id: str) -> bool:
        """Safely removes the /appdata/{app_id} directory on the host filesystem."""
        clean_id = app_id.strip().lower()
        # Safety guards: NEVER purge system root, critical paths, or empty strings
        if not clean_id or clean_id in ("root", "appdata", "srv", "data", "media", "config", "etc", "var", "home", "usr"):
            logger.warning(f"Refusing to purge reserved/critical path keyword: '{clean_id}'")
            return False

        client = self._get_client()
        if not client:
            return False
        try:
            # Execute rm -rf on the specific app directory inside /appdata
            logger.info(f"Purging app config for '{clean_id}' (/appdata/{clean_id})...")
            payload = {
                "Image": "ghcr.io/nchungdev/claraos:latest",
                "Cmd": ["sh", "-c", f'if [ -d "/parent/{clean_id}" ]; then rm -rf "/parent/{clean_id}"; fi'],
                "HostConfig": {
                    "Binds": ["/appdata:/parent:rw"]
                }
            }
            res = await client.post("/containers/create", json=payload)
            if res.status_code != 201:
                logger.error(f"Failed to create purge helper container: {res.text}")
                return False
            cid = res.json().get("Id")
            try:
                await client.post(f"/containers/{cid}/start")
                wait_res = await client.post(f"/containers/{cid}/wait")
                code = wait_res.json().get("StatusCode", 1)
                return code == 0
            finally:
                await client.delete(f"/containers/{cid}", params={"force": "true"})
        except Exception as e:
            logger.error(f"Error purging app config for {clean_id}: {e}")
            return False


docker_manager = DockerManager()
