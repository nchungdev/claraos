from typing import Dict, Any, List

APP_CATALOG: List[Dict[str, Any]] = [
    # 1. ClaraOS Specialized Services

    {
        "id": "media-organizer",
        "name": "Media Organizer",
        "category": "Media",
        "description": "Tự động phân loại, đổi tên và khớp metadata TMDb cho phim & series.",
        "icon": "fa-film",
        "logo_id": "tmdb",
        "default_port": 8093,
        "subdomain": "media-organizer",
        "installed": True,
        "is_running": True,
        "container_name": "media-organizer",
        "image": "ghcr.io/nchungdev/media-organizer:latest"
    },
    {
        "id": "debrid-ingest",
        "name": "Debrid Manager",
        "category": "Downloads",
        "description": "Tải Debrid đám mây & chuyển tiếp về Aria2 tốc độ cao.",
        "icon": "fa-download",
        "logo_id": "torbox",
        "default_port": 8092,
        "subdomain": "torbox-worker",
        "installed": True,
        "is_running": True,
        "container_name": "torbox-worker",
        "image": "ghcr.io/nchungdev/debrid-manager:latest"
    },
    # 2. Existing NAS Host & Core Services
    {
        "id": "omv",
        "name": "OpenMediaVault",
        "category": "System",
        "description": "OpenMediaVault NAS Storage, Disks, RAID & System Administration.",
        "icon": "fa-server",
        "logo_id": "openmediavault",
        "default_port": 80,
        "subdomain": "omv",
        "protected": True,
        "manageable": False,
        "installed": True,
        "is_running": True,
        "image": "openmediavault:host"
    },
    {
        "id": "agy-manager",
        "name": "Agent Hub",
        "category": "System",
        "description": "Antigravity Multi-Agent orchestration & session manager.",
        "icon": "fa-robot",
        "logo_id": "anthropic",
        "subdomain": "agy",
        "default_port": 8585,
        "protected": True,
        "manageable": False,
        "image": "ghcr.io/nchungdev/antigravity-manager:latest"
    },
    {
        "id": "rclone",
        "name": "Rclone Manager",
        "category": "System",
        "description": "Quản lý đồng bộ Cloud Rclone & Google Drive tốc độ cao (Rclone Web GUI & VFS).",
        "icon": "fa-cloud-arrow-up",
        "logo_id": "rclone",
        "subdomain": "rclone",
        "default_port": 5572,
        "installed": True,
        "is_running": True,
        "protected": True,
        "manageable": False,
        "container_name": "cloudflared-rclone",
        "image": "rclone/rclone:latest"
    },
    # 3. Media Streaming & Request
    {
        "id": "plex",
        "name": "Plex Media Server",
        "category": "Media",
        "description": "Stream movies, TV shows, and personal media to all your devices.",
        "icon": "fa-play-circle",
        "logo_id": "plex",
        "image": "lscr.io/linuxserver/plex:latest",
        "default_port": 32400,
        "ports": {"32400": "32400"},
        "volumes": ["/srv/mergerfs/MainPool:/media", "/config/plex:/config"],
        "env": ["PUID=1000", "PGID=1000", "VERSION=docker"]
    },
    {
        "id": "jellyfin",
        "name": "Jellyfin",
        "category": "Media",
        "description": "The Free Software Media System. Stream to any device from your server.",
        "icon": "fa-film",
        "logo_id": "jellyfin",
        "image": "jellyfin/jellyfin:latest",
        "default_port": 8096,
        "ports": {"8096": "8096"},
        "volumes": ["/srv/mergerfs/MainPool:/media", "/config/jellyfin:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "jellyseerr",
        "name": "Jellyseerr",
        "category": "Media",
        "description": "Request management system for your Plex and Jellyfin media library.",
        "icon": "fa-magnifying-glass",
        "logo_id": "jellyseerr",
        "image": "fallenbagel/jellyseerr:latest",
        "default_port": 5055,
        "ports": {"5055": "5055"},
        "volumes": ["/config/jellyseerr:/app/config"],
        "env": ["LOG_LEVEL=info"]
    },
    # 4. Automation & *Arr Stack
    {
        "id": "sonarr",
        "name": "Sonarr",
        "category": "Automation",
        "description": "Smart TV Series manager and automated downloader.",
        "icon": "fa-tv",
        "logo_id": "sonarr",
        "image": "lscr.io/linuxserver/sonarr:latest",
        "default_port": 8989,
        "ports": {"8989": "8989"},
        "volumes": ["/srv/mergerfs/MainPool/Phim/TV:/tv", "/config/sonarr:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "radarr",
        "name": "Radarr",
        "category": "Automation",
        "description": "Movie collection manager and automated downloader.",
        "icon": "fa-video",
        "logo_id": "radarr",
        "image": "lscr.io/linuxserver/radarr:latest",
        "default_port": 7878,
        "ports": {"7878": "7878"},
        "volumes": ["/srv/mergerfs/MainPool/Phim/Movies:/movies", "/config/radarr:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "prowlarr",
        "name": "Prowlarr",
        "category": "Automation",
        "description": "Indexer manager/proxy integrating with Sonarr, Radarr & Lidarr.",
        "icon": "fa-cloud",
        "logo_id": "prowlarr",
        "image": "lscr.io/linuxserver/prowlarr:latest",
        "default_port": 9696,
        "ports": {"9696": "9696"},
        "volumes": ["/config/prowlarr:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "tdarr",
        "name": "Tdarr",
        "category": "Automation",
        "description": "Distributed GPU/CPU hardware-accelerated transcoding system.",
        "icon": "fa-film",
        "logo_id": "tdarr",
        "image": "ghcr.io/haveagitgat/tdarr:latest",
        "default_port": 8265,
        "ports": {"8265": "8265"},
        "volumes": ["/srv/mergerfs/MainPool:/media", "/config/tdarr:/app/configs"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    # 5. Books, Comics & Manga
    {
        "id": "komga",
        "name": "Komga",
        "category": "Books",
        "description": "Free and open source comics/manga server with OPDS support.",
        "icon": "fa-book-open",
        "logo_id": "komga",
        "image": "gotson/komga:latest",
        "default_port": 25600,
        "ports": {"25600": "25600"},
        "volumes": ["/srv/mergerfs/MainPool/Truyen:/data", "/config/komga:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "kavita",
        "name": "Kavita",
        "category": "Books",
        "description": "Fast, feature-rich cross-platform reading server for manga & comics.",
        "icon": "fa-book",
        "logo_id": "kavita",
        "image": "jvmilazz0/kavita:latest",
        "default_port": 5000,
        "ports": {"5000": "5000"},
        "volumes": ["/srv/mergerfs/MainPool/Truyen:/data", "/config/kavita:/kavita/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "calibre-web",
        "name": "Calibre-Web",
        "category": "Books",
        "description": "Clean web interface for reading and managing Calibre e-book libraries.",
        "icon": "fa-book-bookmark",
        "logo_id": "calibre-web",
        "image": "lscr.io/linuxserver/calibre-web:latest",
        "default_port": 8083,
        "ports": {"8083": "8083"},
        "volumes": ["/srv/mergerfs/MainPool/Books:/books", "/config/calibre-web:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    # 6. File Management & Download Tools
    {
        "id": "filebrowser",
        "name": "FileBrowser",
        "category": "Tools",
        "description": "Provides a file managing interface within your storage pool.",
        "icon": "fa-folder-open",
        "logo_id": "filebrowser",
        "image": "filebrowser/filebrowser:latest",
        "default_port": 8080,
        "ports": {"8080": "80"},
        "volumes": ["/srv/mergerfs/MainPool:/srv", "/config/filebrowser:/config"],
        "env": []
    },
    {
        "id": "openlist",
        "name": "OpenList",
        "category": "Tools",
        "description": "High-speed 115 cloud drive indexing & streaming server.",
        "icon": "fa-folder-tree",
        "logo_id": "openlist",
        "image": "openlistteam/openlist:latest",
        "default_port": 5244,
        "ports": {"5244": "5244"},
        "volumes": ["/config/openlist:/app/data"],
        "env": []
    },
    {
        "id": "ariang",
        "name": "AriaNg",
        "category": "Downloads",
        "description": "Modern Web frontend for Aria2 high-speed download engine.",
        "icon": "fa-download",
        "logo_id": "ariang",
        "subdomain": "ariang",
        "default_port": 6880
    },
    {
        "id": "metube",
        "name": "MeTube",
        "category": "Downloads",
        "description": "Web GUI for youtube-dl / yt-dlp with playlist support.",
        "icon": "fa-youtube",
        "logo_id": "metube",
        "image": "ghcr.io/alexta69/metube:latest",
        "default_port": 8081,
        "ports": {"8081": "8081"},
        "volumes": ["/srv/mergerfs/MainPool/Downloads:/downloads"],
        "env": ["OUTPUT_TEMPLATE=%(title)s.%(ext)s"]
    },
    {
        "id": "flaresolverr",
        "name": "FlareSolverr",
        "category": "Tools",
        "description": "Proxy server to bypass Cloudflare and DDoS-GUARD protection.",
        "icon": "fa-shield-halved",
        "logo_id": "flaresolverr",
        "default_port": 8191,
        "protected": True,
        "manageable": False,
        "has_gui": False
    },
    # 7. Additional Store-Only Apps (Available for 1-Click Install)
    {
        "id": "qbittorrent",
        "name": "qBittorrent",
        "category": "Downloads",
        "description": "Fast, lightweight BitTorrent client with Web UI and search engine.",
        "icon": "fa-download",
        "logo_id": "qbittorrent",
        "image": "lscr.io/linuxserver/qbittorrent:latest",
        "default_port": 8085,
        "ports": {"8085": "8080", "6881": "6881"},
        "volumes": ["/srv/mergerfs/MainPool/Downloads:/downloads", "/config/qbittorrent:/config"],
        "env": ["PUID=1000", "PGID=1000", "WEBUI_PORT=8080"]
    },
    {
        "id": "bazarr",
        "name": "Bazarr",
        "category": "Automation",
        "description": "Companion to Sonarr and Radarr for automated subtitle management.",
        "icon": "fa-closed-captioning",
        "logo_id": "bazarr",
        "image": "lscr.io/linuxserver/bazarr:latest",
        "default_port": 6767,
        "ports": {"6767": "6767"},
        "volumes": ["/srv/mergerfs/MainPool/Phim:/movies", "/config/bazarr:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "vaultwarden",
        "name": "Vaultwarden",
        "category": "Tools",
        "description": "Lightweight Bitwarden-compatible password manager written in Rust.",
        "icon": "fa-key",
        "logo_id": "vaultwarden",
        "image": "vaultwarden/server:latest",
        "default_port": 8088,
        "ports": {"8088": "80"},
        "volumes": ["/config/vaultwarden:/data"],
        "env": []
    }
]

import os
import json
import logging
import re
import urllib.request

logger = logging.getLogger("claraos.catalog")

COMMUNITY_SOURCES = [
    "https://raw.githubusercontent.com/Lissy93/portainer-templates/main/templates.json",
    "https://raw.githubusercontent.com/portainer/templates/master/templates-2.0.json"
]

CACHE_PATHS = [
    "/config/community_apps_cache.json",
    os.path.join(os.path.dirname(__file__), "community_apps_cache.json"),
    "/tmp/community_apps_cache.json"
]

CATEGORY_MAP = {
    'media': 'Media', 'video': 'Media', 'audio': 'Media', 'music': 'Media', 'streaming': 'Media', 'multimedia': 'Media',
    'automation': 'Automation', 'arr': 'Automation', 'iot': 'Automation', 'smart home': 'Automation', 'home automation': 'Automation',
    'books': 'Books', 'comics': 'Books', 'ebooks': 'Books', 'audiobooks': 'Books',
    'downloads': 'Downloads', 'downloaders': 'Downloads', 'torrent': 'Downloads',
    'ai': 'AI', 'llm': 'AI', 'machine learning': 'AI',
    'tools': 'Tools', 'system': 'Tools', 'network': 'Tools', 'security': 'Tools', 'dashboard': 'Tools', 'database': 'Tools'
}

def map_category(cats):
    for c in cats or []:
        c_low = c.lower()
        for k, v in CATEGORY_MAP.items():
            if k in c_low:
                return v
    return 'Tools'

def get_community_catalog() -> List[Dict[str, Any]]:
    for path in CACHE_PATHS:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return data
            except Exception as e:
                logger.error(f"Error reading community apps cache from {path}: {e}")
    return []

def sync_community_catalog() -> int:
    apps = []
    seen = set()
    for src in COMMUNITY_SOURCES:
        try:
            req = urllib.request.Request(src, headers={"User-Agent": "ClaraOS-Store/1.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            templates = [t for t in data.get("templates", []) if t.get("image")]
            for t in templates:
                title = t.get("title") or t.get("name") or ""
                app_id = re.sub(r"[^a-z0-9_-]", "", (t.get("name") or title).lower().replace(" ", "-"))
                if not app_id or app_id in seen:
                    continue
                seen.add(app_id)

                ports = {}
                default_port = None
                for p in t.get("ports", []):
                    parts = p.split("/")[0].split(":")
                    if len(parts) == 2:
                        h, c = parts[0], parts[1]
                        ports[h] = c
                        if not default_port and h.isdigit():
                            default_port = int(h)

                env = []
                for e in t.get("env", []):
                    if isinstance(e, dict) and e.get("name"):
                        v = e.get("default", "")
                        env.append(f"{e['name']}={v}")

                volumes = []
                for v in t.get("volumes", []):
                    if isinstance(v, dict) and v.get("container"):
                        volumes.append(f"/config/{app_id}:{v['container']}")
                if not volumes:
                    volumes = [f"/config/{app_id}:/config"]

                cat = map_category(t.get("categories", []))

                apps.append({
                    "id": app_id,
                    "name": title,
                    "category": cat,
                    "description": t.get("description", ""),
                    "logo": t.get("logo", ""),
                    "image": t["image"],
                    "default_port": default_port,
                    "ports": ports,
                    "volumes": volumes,
                    "env": env,
                    "community": True
                })
        except Exception as e:
            logger.error(f"Failed to fetch community source {src}: {e}")

    if apps:
        for path in CACHE_PATHS:
            try:
                parent = os.path.dirname(path)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(apps, f, indent=2, ensure_ascii=False)
                break
            except Exception:
                continue
    return len(apps)

def get_full_catalog() -> List[Dict[str, Any]]:
    full = list(APP_CATALOG)
    existing_ids = {a["id"].lower() for a in full}
    for ca in get_community_catalog():
        if ca["id"].lower() not in existing_ids:
            full.append(ca)
            existing_ids.add(ca["id"].lower())
    return full
