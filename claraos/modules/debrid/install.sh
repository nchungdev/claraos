#!/bin/sh
# Install the Debrid library indexer as a host systemd service (needs root).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
install -m 755 "$HERE/library_indexer.py" /usr/local/bin/debrid-library-indexer
cat > /etc/systemd/system/debrid-library-indexer.service <<UNIT
[Unit]
Description=Index the Plex/Jellyfin library for Debrid Manager
After=local-fs.target docker.service

[Service]
ExecStart=/usr/local/bin/debrid-library-indexer
Restart=always
RestartSec=10
Nice=10
IOSchedulingClass=idle

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now debrid-library-indexer
systemctl restart debrid-library-indexer
