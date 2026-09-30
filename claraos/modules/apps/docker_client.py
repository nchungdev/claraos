import os
import logging
from typing import Dict, List, Any, Optional
import httpx

logger = logging.getLogger("claraos.docker")
DOCKER_SOCKET = os.getenv("DOCKER_SOCKET_PATH", "/var/run/docker.sock")


class DockerManager:
    def __init__(self, socket_path: str = DOCKER_SOCKET):
        self.socket_path = socket_path

    def _get_client(self) -> Optional[httpx.AsyncClient]:
        if not os.path.exists(self.socket_path):
            return None
        transport = httpx.AsyncHTTPTransport(uds=self.socket_path)
        return httpx.AsyncClient(transport=transport, base_url="http://docker", timeout=30.0)

    async def list_containers(self, all_containers: bool = True) -> List[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            return []
        try:
            async with client:
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
            async with client:
                res = await client.post(f"/containers/{container_id}/start")
                return res.status_code in (204, 304)
        except Exception as e:
            logger.error(f"Error starting container {container_id}: {e}")
            return False

    async def stop_container(self, container_id: str) -> bool:
        client = self._get_client()
        if not client: return False
        try:
            async with client:
                res = await client.post(f"/containers/{container_id}/stop")
                return res.status_code in (204, 304)
        except Exception as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            return False

    async def restart_container(self, container_id: str) -> bool:
        client = self._get_client()
        if not client: return False
        try:
            async with client:
                res = await client.post(f"/containers/{container_id}/restart")
                return res.status_code in (204, 304)
        except Exception as e:
            logger.error(f"Error restarting container {container_id}: {e}")
            return False

    async def remove_container(self, container_id: str) -> bool:
        client = self._get_client()
        if not client: return False
        try:
            async with client:
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
            async with client:
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


docker_manager = DockerManager()
