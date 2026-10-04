# Debrid library indexer
Scans the Plex/Jellyfin folders (`/srv/mergerfs/MainPool/Phim/{Movies,TV Shows}`) into `/var/lib/media-staging/.library.db`
(read by the Debrid Manager container as `/staging/.library.db`, and by Media Organizer for auto-matching).
- Incremental: a title folder is re-read only when its mtime changes; full pass every 5 min.
- Instant rescan: Radarr/Sonarr webhook -> `POST /api/library/rescan` on Debrid Manager -> trigger file.
- Titles come from folder names, `{tmdb-}`/`{tvdb-}` tags, `movie.nfo`/`tvshow.nfo` (original + localised titles) and
  names the Media Organizer already matched.
Install/refresh: `sudo sh install.sh`.
