# 🌌 AetherBox

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-Modular%20Monolith-indigo?style=for-the-badge" alt="Architecture">
  <img src="https://img.shields.io/badge/Container-Single%20Container-emerald?style=for-the-badge" alt="Single Container">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</p>

> **AetherBox** is an all-in-one, modular media ingestion, debrid caching, and cloud sync engine designed for self-hosters and homelab enthusiasts running Plex, Jellyfin, or Emby.

---

## ✨ Features & Architecture

AetherBox is packaged as a **single lightweight Docker container**, built on top of a **Modular Monolith** architecture. Each module can be independently enabled or disabled at installation time or dynamically toggled via the Web UI at runtime:

- 🚀 **Cloud Sync Pro (`mod_sync`):**
  - Real-time Rclone process telemetry directly from Linux `/proc`.
  - Zero-lag delta upload speed calculations.
  - Active task governance (`SIGSTOP` pause, `SIGCONT` resume, `SIGTERM` stop).
  - VFS mount inspection and dynamic bandwidth control.

- 🎬 **Media Organizer (`mod_organizer`):**
  - Automated Staging folder inspector.
  - TMDb metadata search & resolver.
  - Standardized Plex/Jellyfin naming convention builder (`Movie (Year)` & `Show/Season XX/Show - SxxExx`).
  - Atomic hardlinking/moving into your storage pool (MergerFS / NAS).

- 📥 **Debrid Ingest (`mod_debrid`):**
  - Torbox & Debrid cloud downloader integration.
  - Instant magnet & torrent ingestion pipeline.
  - Automated bridging into local staging directories.

- 🎨 **AriaNg-Inspired Web Dashboard:**
  - Modern, responsive dark mode with glassmorphism aesthetics.
  - Collapsible sidebar with real-time badges (speed, file counts, system health).
  - Dynamic navigation tabs based on which modules are enabled.

---

## 🚀 Quick Start (Docker Compose)

Save this as `docker-compose.yml`:

```yaml
services:
  aetherbox:
    image: ghcr.io/nchungdev/aetherbox:latest
    container_name: aetherbox
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Asia/Ho_Chi_Minh
      # Choose which modules to enable on startup:
      - MODULE_DEBRID_ENABLED=true
      - MODULE_ORGANIZER_ENABLED=true
      - MODULE_SYNC_ENABLED=true
    volumes:
      - ./config:/config
      - /mnt/storage:/data
      # Mount host /proc for Rclone process inspection:
      - /proc:/proc:ro
```

Run:
```bash
docker compose up -d
```
Open `http://localhost:8080` in your browser.

---

## ⚙️ Module Dynamic Toggling

You don't need to restart the container to enable or disable features.
1. Navigate to **Settings & Modules** in the sidebar.
2. Toggle any module switch on or off.
3. The background worker will gracefully start or stop, and the navigation sidebar will immediately update!

---

## 📄 License
MIT License © [nchungdev](https://github.com/nchungdev)
