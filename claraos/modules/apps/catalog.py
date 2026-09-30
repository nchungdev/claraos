from typing import Dict, Any, List

APP_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "cloud-sync",
        "name": "Cloud Sync Pro",
        "category": "System",
        "description": "Real-time Linux /proc I/O monitoring & Rclone Cloud Sync.",
        "icon": "fa-cloud-arrow-up",
        "logo_id": "rclone",
        "native": True,
        "default_port": 8090,
        "url": "/#sync"
    },
    {
        "id": "media-organizer",
        "name": "Media Organizer",
        "category": "Media",
        "description": "TMDb metadata scraper & automatic media renamer.",
        "icon": "fa-film",
        "logo_id": "tmdb",
        "native": True,
        "default_port": 8090,
        "url": "/#organizer"
    },
    {
        "id": "debrid-ingest",
        "name": "Debrid Ingestion",
        "category": "Downloads",
        "description": "Torbox high-speed Cloud Debrid downloader.",
        "icon": "fa-download",
        "logo_id": "torbox",
        "native": True,
        "default_port": 8090,
        "url": "/#debrid"
    },
    {
        "id": "plex",
        "name": "Plex Media Server",
        "category": "Media",
        "description": "Stream movies, TV shows, and personal media to all your devices.",
        "icon": "fa-play-circle",
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
        "description": "The Free Software Media System. Stream to any device from your own server.",
        "icon": "fa-film",
        "image": "jellyfin/jellyfin:latest",
        "default_port": 8096,
        "ports": {"8096": "8096"},
        "volumes": ["/srv/mergerfs/MainPool:/media", "/config/jellyfin:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "sonarr",
        "name": "Sonarr",
        "category": "Automation",
        "description": "Smart TV Series manager and automated downloader for Usenet and BitTorrent.",
        "icon": "fa-tv",
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
        "description": "Indexer manager/proxy built on the popular *arr .net stack.",
        "icon": "fa-cloud",
        "image": "lscr.io/linuxserver/prowlarr:latest",
        "default_port": 9696,
        "ports": {"9696": "9696"},
        "volumes": ["/config/prowlarr:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "jellyseerr",
        "name": "Jellyseerr",
        "category": "Media",
        "description": "Free and open source software for managing requests for your media library.",
        "icon": "fa-magnifying-glass",
        "image": "fallenbagel/jellyseerr:latest",
        "default_port": 5055,
        "ports": {"5055": "5055"},
        "volumes": ["/config/jellyseerr:/app/config"],
        "env": ["LOG_LEVEL=info"]
    },
    {
        "id": "komga",
        "name": "Komga",
        "category": "Books",
        "description": "Free and open source comics/manga server with OPDS support.",
        "icon": "fa-book-open",
        "image": "gotson/komga:latest",
        "default_port": 25600,
        "ports": {"25600": "25600"},
        "volumes": ["/srv/mergerfs/MainPool/Truyen:/data", "/config/komga:/config"],
        "env": ["PUID=1000", "PGID=1000"]
    },
    {
        "id": "filebrowser",
        "name": "FileBrowser",
        "category": "Tools",
        "description": "Provides a file managing interface within a specified directory.",
        "icon": "fa-folder-open",
        "image": "filebrowser/filebrowser:latest",
        "default_port": 8080,
        "ports": {"8082": "80"},
        "volumes": ["/srv/mergerfs/MainPool:/srv", "/config/filebrowser:/config"],
        "env": []
    },
    {
        "id": "metube",
        "name": "MeTube",
        "category": "Tools",
        "description": "Web GUI for youtube-dl / yt-dlp with playlist support.",
        "icon": "fa-youtube",
        "image": "ghcr.io/alexta69/metube:latest",
        "default_port": 8081,
        "ports": {"8081": "8081"},
        "volumes": ["/srv/mergerfs/MainPool/Downloads:/downloads"],
        "env": ["OUTPUT_TEMPLATE=%(title)s.%(ext)s"]
    }
]
