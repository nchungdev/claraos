# Gateway auto-mapper
Watches `docker events` and writes `/docker-files/gateway/auto/apps-auto.conf` (host -> published port),
then reloads `wildcard-gateway`. Works for apps installed by ClaraOS or by OpenMediaVault compose.
- Subdomain = container name or compose service name. Labels: `gateway.enable=false`, `gateway.subdomain=x`, `gateway.port=N`.
- Manual entries in `nginx.conf` always win; this only feeds the `default` fallback.
- Host-network containers (no published ports) must be added manually.
- Service: `gateway-automap.service`; reinstall with `sudo sh install.sh`.
