#!/bin/sh
# Install the ClaraOS gateway auto-mapper as a host systemd service (needs root).
# Source of truth: modules/gateway/automap.py. Re-run after editing it.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
install -m 755 "$HERE/automap.py" /usr/local/bin/gateway-automap
systemctl restart gateway-automap
