# 🧠 ClaraOS

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-Modular%20Monolith-purple?style=for-the-badge" alt="Architecture">
  <img src="https://img.shields.io/badge/AI%20Engines-Antigravity%20%7C%20Claude-indigo?style=for-the-badge" alt="AI Engines">
  <img src="https://img.shields.io/badge/Container-Single%20Container-emerald?style=for-the-badge" alt="Single Container">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</p>

> **ClaraOS** is the open-source, AI-native homelab operating system and orchestration engine. It unifies **Coding AI Agents (Google Antigravity & Claude Code)**, **1-Click Docker App Store (Plex, *Arr stack)**, **Media Ingestion (Debrid/TMDb)**, and **Cloud Sync Acceleration** into a single, cohesive, web-based dashboard.

---

## ✨ Modular Architecture

ClaraOS runs as a **single, ultra-lightweight Docker container** (~120MB) utilizing an asynchronous **Modular Monolith** pattern. Any module can be turned on or off at installation or dynamically toggled via the Web UI at runtime without restarting the container:

### 1. 🤖 Clara AI Agent Studio (`mod_agents`)
- **Universal Multi-Agent Hub:** Seamlessly execute and monitor tasks across **Google Antigravity (`agy`)**, **Anthropic Claude Code (`claude`)**, and Codex from one intuitive Web GUI.
- **Quota Tracking:** Real-time token monitoring for Gemini 2.5 Flash/Pro and Claude 3.7 Sonnet.
- **Agentic SRE:** Let AI diagnose container crashloops, tune Rclone transfers, or organize incoming media via natural language.

### 2. 🧩 1-Click Docker App Store (`mod_apps`)
- **Native Docker Socket Integration:** Discovers and controls upstream containers on your host via `/var/run/docker.sock`.
- **450+ Expanded App Catalog:** Combines curated homelab templates with rich upstream community catalogs (Portainer & Lissy93).
  - **Dynamic Catalog Sync:** 1-Click "Đồng bộ Catalog" (`POST /api/modules/apps/catalog/sync`) to refresh templates on-the-fly with persistent host caching.
  - **Categorized Discovery:** Filter across `All`, `Media`, `Automation`, `AI`, `Reading`, and `System & Tools`.
  - **Intelligent GUI Detection:** Headless containers (`has_gui: false`) show operational state without misleading WebUI redirects.
  - **Zero Bloat:** Third-party apps run as independent official containers; ClaraOS itself remains clean and lightweight.

### 3. 🚀 Cloud Sync Pro (`mod_sync`)
- Real-time Rclone process telemetry directly from Linux `/proc`.
- Zero-lag delta upload speed calculations.
- Active task governance (`SIGSTOP` pause, `SIGCONT` resume, `SIGTERM` stop).
- VFS mount inspection, dynamic bandwidth control, and remote quota caching (`Available: used/quota`).

### 4. 🎬 Media Organizer (`mod_organizer`)
- Automated Staging folder inspector.
- TMDb metadata search & resolver.
- Standardized Plex/Jellyfin naming convention builder (`Movie (Year)` & `Show/Season XX/Show - SxxExx`).
- Atomic hardlinking/moving into your storage pool (MergerFS / NAS).

### 5. 📥 Debrid Ingest (`mod_debrid`)
- Torbox & Debrid cloud downloader integration.
- Instant magnet & torrent ingestion pipeline.
- Automated bridging into local staging directories.

### 6. 🎨 Unified Glassmorphism & Third-Party Theming
- Strict design language across the ecosystem: `#070c18` canvas, blur glass panels (`rgba(15, 23, 42, 0.65)`), `Plus Jakarta Sans` typography, and vibrant cyan/emerald accents.
- **Zero-Code OpenList Integration:** Seamless styling injection via `customize_head` in SQLite persistent database—retaining 100% upstream Docker compatibility with zero source rebuilds.
- **Standardized Footer Telemetry:** Unified status indicators, `Available: used/quota` remote metrics, and conditional HDD resource attribution across all suite apps.

---

## 🚀 Quick Start (Docker Compose)

Save this as `docker-compose.yml`:

```yaml
services:
  claraos:
    image: ghcr.io/nchungdev/claraos:latest
    container_name: claraos
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Asia/Ho_Chi_Minh
      # Choose which modules to enable on startup:
      - MODULE_AGENTS_ENABLED=true
      - MODULE_APPS_ENABLED=true
      - MODULE_SYNC_ENABLED=true
      - MODULE_ORGANIZER_ENABLED=true
      - MODULE_DEBRID_ENABLED=true
    volumes:
      - ./config:/config
      - /mnt/storage:/data
      # Host proc for Rclone telemetry:
      - /proc:/proc:ro
      # Host Docker socket for 1-Click App Store:
      - /var/run/docker.sock:/var/run/docker.sock
```

Run:
```bash
docker compose up -d
```
Open `http://localhost:8080` in your browser.

---

## ⚙️ Module Dynamic Toggling

No container restart needed:
1. Navigate to **Settings & Modules** in the sidebar.
2. Toggle any module on or off.
3. Background workers instantly spin up or terminate, and the navigation sidebar updates automatically in real-time.

---

## 📄 License
MIT License © [nchungdev](https://github.com/nchungdev)
