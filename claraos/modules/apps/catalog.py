"""Curated apps pinned at the top of the Compose-aware ClaraOS App Hub."""

from typing import Any, Dict, List


APP_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "organizer", "name": "Organizer", "category": "Media workflow",
        "description": "Duyệt staging, khớp TMDb và đề xuất vị trí Plex/Jellyfin.",
        "icon": "fa-film", "logo_id": "tmdb", "container_name": "media-organizer",
        "default_port": 8093, "subdomain": "media-organizer",
        "url": "https://media-organizer.data1box.win", "compose_key": "media-organizer",
        "pinned": True, "manageable": False, "protected": True,
    },
    {
        "id": "debrid", "name": "Debrid", "category": "Download workflow",
        "description": "TorBox worker: chuyển file cloud đã hoàn tất vào SSD staging.",
        "icon": "fa-cloud-arrow-down", "logo_id": "torbox", "container_name": "torbox-worker",
        "default_port": 8092, "subdomain": "torbox-worker",
        "url": "https://torbox-worker.data1box.win", "compose_key": "torbox-worker",
        "pinned": True, "manageable": False, "protected": True,
    },
    {
        "id": "rclone", "name": "Rclone", "category": "Cloud storage",
        "description": "Web GUI và registry mount Rclone; quản lý remote cloud tập trung.",
        "icon": "fa-cloud-arrow-up", "logo_id": "rclone", "container_name": "rclone",
        "default_port": 5572, "subdomain": "rclone", "url": "https://rclone.data1box.win",
        "compose_key": "rclone", "pinned": True, "manageable": False, "protected": True,
    },
    {
        "id": "ariang", "name": "AriaNg", "category": "Download workflow",
        "description": "Giao diện Aria2 cho hàng đợi tải về SSD staging.",
        "icon": "fa-download", "logo_id": "ariang", "container_name": "ariang",
        "subdomain": "ariang", "url": "https://ariang.data1box.win", "compose_key": "ariang",
        "pinned": True, "manageable": False, "protected": True,
    },
    {
        "id": "agent", "name": "Agent", "category": "Automation",
        "description": "AGY Manager: điều phối Antigravity CLI và theo dõi quota.",
        "icon": "fa-robot", "logo_id": "anthropic", "container_name": "agy-manager",
        "default_port": 8585, "subdomain": "agy", "url": "https://agy.data1box.win",
        "compose_key": "agy-manager", "pinned": True, "manageable": False, "protected": True,
    },
]
