#!/usr/bin/env python3
"""Index the Plex/Jellyfin library folders into SQLite so Debrid Manager can tell what is already on the NAS.

Source of truth is the folder tree (Plex and Jellyfin read the same folders). Folder names carry {tmdb-ID}/{tvdb-ID}
tags, filenames carry SxxExx and quality tokens, and movie.nfo / tvshow.nfo carry the original title, which is how a
Vietnamese-titled folder is matched to an English torrent name.

Incremental: a title folder is re-read only when its mtime changed. A rescan can be requested by touching the
trigger file (the worker does this when Radarr/Sonarr call its webhook).
"""
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET

LIB_ROOT = os.environ.get("LIB_ROOT", "/srv/mergerfs/MainPool/Phim")
DB_PATH = os.environ.get("LIB_DB", "/var/lib/media-staging/.library.db")
TRIGGER = os.environ.get("LIB_TRIGGER", "/var/lib/media-staging/.library-rescan")
ORGANIZER_DB = os.environ.get("ORGANIZER_DB", "/var/lib/media-organizer/organizer.db")
INTERVAL = int(os.environ.get("LIB_INTERVAL", "300"))
VIDEO = {".mkv", ".mp4", ".avi", ".m4v", ".ts", ".mov", ".wmv", ".mpg", ".mpeg", ".webm", ".m2ts"}


def norm(text):
    """Lowercase, strip accents/punctuation. MUST stay identical to the copy in the Debrid worker."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("đ", "d").replace("Đ", "d")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


RES_RE = re.compile(r"(?<![0-9])(2160p|4k|uhd|1080p|1080i|1080|720p|720|576p|480p|480)(?![0-9])", re.I)
SRC_RE = re.compile(r"(remux|blu-?ray|bdrip|brrip|web-?dl|web-?rip|webrip|hdtv|dvdrip|dvd|hdrip|cam)", re.I)
CODEC_RE = re.compile(r"(x265|hevc|h\.?265|x264|h\.?264|av1|xvid)", re.I)
EP_RES = [
    re.compile(r"[Ss](\d{1,2})[ ._-]*[Ee](\d{1,4})(?:[ ._-]*[Ee-](\d{1,4}))?"),
    re.compile(r"(?<![0-9])(\d{1,2})x(\d{2,3})(?![0-9])"),
]


def res_of(name):
    m = RES_RE.search(name)
    if not m:
        return None
    v = m.group(1).lower()
    if v in ("2160p", "4k", "uhd"):
        return 2160
    if v.startswith("1080"):
        return 1080
    if v.startswith("720"):
        return 720
    if v.startswith("576"):
        return 576
    return 480


def quality_of(name):
    s = SRC_RE.search(name)
    c = CODEC_RE.search(name)
    src = s.group(1).lower().replace("-", "") if s else None
    return res_of(name), src, (c.group(1).lower() if c else None)


def episode_of(name):
    for rx in EP_RES:
        m = rx.search(name)
        if m:
            season, ep = int(m.group(1)), int(m.group(2))
            last = int(m.group(3)) if m.lastindex and m.lastindex >= 3 and m.group(3) else ep
            return season, ep, max(ep, last)
    return None


FOLDER_RE = re.compile(r"^(?P<title>.*?)\s*(?:\((?P<year>\d{4})\))?\s*(?P<tags>(?:\{[^}]*\}\s*)*)$")


def parse_folder(name):
    m = FOLDER_RE.match(name)
    title = (m.group("title") if m else name).strip()
    year = int(m.group("year")) if m and m.group("year") else None
    tags = name
    tmdb = re.search(r"\{tmdb-(\d+)\}", tags)
    tvdb = re.search(r"\{tvdb-(\d+)\}", tags)
    imdb = re.search(r"\{imdb-(tt\d+)\}", tags)
    return title, year, (int(tmdb.group(1)) if tmdb else None), (int(tvdb.group(1)) if tvdb else None), (imdb.group(1) if imdb else None)


def nfo_titles(folder, kind):
    """Titles from movie.nfo / tvshow.nfo (original + localised). Returns (titles, tmdb)."""
    out, tmdb = [], None
    for fname in (("movie.nfo",) if kind == "movie" else ("tvshow.nfo",)):
        p = os.path.join(folder, fname)
        if not os.path.isfile(p):
            continue
        try:
            root = ET.parse(p).getroot()
        except (ET.ParseError, OSError):
            continue
        for tag in ("title", "originaltitle", "sorttitle"):
            for el in root.iter(tag):
                if el.text and el.text.strip():
                    out.append(el.text.strip())
        for el in root.iter("uniqueid"):
            if (el.get("type") or "").lower() == "tmdb" and el.text and el.text.strip().isdigit():
                tmdb = int(el.text.strip())
    return out, tmdb


def init(c):
    c.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS titles (
      key TEXT PRIMARY KEY, kind TEXT, path TEXT, title TEXT, year INTEGER, tmdb_id INTEGER, tvdb_id INTEGER, imdb_id TEXT, mtime REAL);
    CREATE TABLE IF NOT EXISTS aliases (key TEXT, alias TEXT, source TEXT);
    CREATE INDEX IF NOT EXISTS aliases_alias ON aliases(alias);
    CREATE INDEX IF NOT EXISTS aliases_key ON aliases(key);
    CREATE TABLE IF NOT EXISTS files (
      path TEXT PRIMARY KEY, key TEXT, season INTEGER, episode INTEGER, episode_end INTEGER,
      resolution INTEGER, source TEXT, codec TEXT, size INTEGER, mtime REAL);
    CREATE INDEX IF NOT EXISTS files_key ON files(key);
    CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
    """)


def scan_title(c, kind, folder, name):
    key = f"{kind}:{name}"
    title, year, tmdb, tvdb, imdb = parse_folder(name)
    nfo, nfo_tmdb = nfo_titles(folder, kind)
    try:
        mtime = max(os.stat(folder).st_mtime, *(os.stat(os.path.join(folder, d)).st_mtime for d in os.listdir(folder)
                                                 if os.path.isdir(os.path.join(folder, d))), 0)
    except (OSError, ValueError):
        mtime = os.stat(folder).st_mtime
    row = c.execute("SELECT mtime FROM titles WHERE key=?", (key,)).fetchone()
    if row and abs(row[0] - mtime) < 0.5:
        return False
    c.execute("DELETE FROM files WHERE key=?", (key,))
    c.execute("DELETE FROM aliases WHERE key=? AND source!='organizer'", (key,))
    c.execute("INSERT OR REPLACE INTO titles VALUES (?,?,?,?,?,?,?,?,?)", (key, kind, folder, title, year, tmdb or nfo_tmdb, tvdb, imdb, mtime))
    seen = set()
    for alias, src in [(title, "folder")] + [(t, "nfo") for t in nfo]:
        n = norm(alias)
        if n and n not in seen:
            seen.add(n)
            c.execute("INSERT INTO aliases VALUES (?,?,?)", (key, n, src))
    for dirpath, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in ("extras", "featurettes", "trailers", "sample", "samples")]
        for f in files:
            if os.path.splitext(f)[1].lower() not in VIDEO or f.startswith(".") or "-trailer" in f.lower():
                continue
            p = os.path.join(dirpath, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            res, src, codec = quality_of(f)
            if res is None:
                res = quality_of(os.path.basename(dirpath))[0]
            ep = episode_of(f) if kind == "tv" else None
            c.execute("INSERT OR REPLACE INTO files VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (p, key, ep[0] if ep else None, ep[1] if ep else None, ep[2] if ep else None, res, src, codec, st.st_size, st.st_mtime))
    return True


def organizer_aliases(c):
    """Names the Media Organizer already matched: staging file name -> library folder. Gives English release titles."""
    if not os.path.isfile(ORGANIZER_DB):
        return 0
    try:
        o = sqlite3.connect(f"file:{ORGANIZER_DB}?mode=ro", uri=True, timeout=5)
        rows = o.execute("SELECT path, library_path FROM files WHERE library_path IS NOT NULL AND library_path!=''").fetchall()
        o.close()
    except sqlite3.Error:
        return 0
    added = 0
    c.execute("DELETE FROM aliases WHERE source='organizer'")
    for src, lib in rows:
        rel = lib.replace("/library/", "", 1)
        parts = rel.split("/")
        if len(parts) < 2:
            continue
        kind = "movie" if parts[0] == "Movies" else "tv" if parts[0] == "TV Shows" else None
        if not kind or not c.execute("SELECT 1 FROM titles WHERE key=?", (f"{kind}:{parts[1]}",)).fetchone():
            continue
        base = os.path.basename(os.path.dirname(src)) if os.path.dirname(src) != "/staging/aria2" else os.path.splitext(os.path.basename(src))[0]
        for cand in {base, os.path.splitext(os.path.basename(src))[0]}:
            t = re.split(r"[ ._]((?:19|20)\d{2}|[Ss]\d{1,2}[Ee]\d{1,3}|2160p|1080p|720p|480p)", cand, maxsplit=1)[0]
            n = norm(re.sub(r"^\[[^\]]*\]", "", t))
            if n:
                c.execute("INSERT INTO aliases VALUES (?,?,?)", (f"{kind}:{parts[1]}", n, "organizer"))
                added += 1
    return added


def scan(full=False):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=30)
    init(c)
    if full:
        c.execute("UPDATE titles SET mtime=-1")
    changed = 0
    present = set()
    for kind, sub in (("movie", "Movies"), ("tv", "TV Shows")):
        root = os.path.join(LIB_ROOT, sub)
        if not os.path.isdir(root):
            continue
        for name in sorted(os.listdir(root)):
            folder = os.path.join(root, name)
            if name.startswith(".") or not os.path.isdir(folder):
                continue
            present.add(f"{kind}:{name}")
            try:
                if scan_title(c, kind, folder, name):
                    changed += 1
            except OSError as exc:
                print(f"skip {folder}: {exc}", flush=True)
    gone = [k for (k,) in c.execute("SELECT key FROM titles") if k not in present]
    for k in gone:
        for tbl in ("titles", "files", "aliases"):
            c.execute(f"DELETE FROM {tbl} WHERE key=?", (k,))
    org = organizer_aliases(c)
    movies = c.execute("SELECT COUNT(*) FROM titles WHERE kind='movie'").fetchone()[0]
    shows = c.execute("SELECT COUNT(*) FROM titles WHERE kind='tv'").fetchone()[0]
    nfiles = c.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    c.execute("INSERT OR REPLACE INTO meta VALUES ('last_scan', ?)", (str(time.time()),))
    c.execute("INSERT OR REPLACE INTO meta VALUES ('stats', ?)", (json.dumps({"movies": movies, "shows": shows, "files": nfiles}),))
    c.commit()
    c.close()
    try:
        os.chmod(DB_PATH, 0o644)
    except OSError:
        pass
    print(f"scan done: {movies} movies, {shows} shows, {nfiles} files, {changed} folders re-read, {len(gone)} removed, {org} organizer aliases", flush=True)


def main():
    if "--once" in sys.argv:
        scan(full="--full" in sys.argv)
        return
    scan()
    last = time.time()
    while True:
        time.sleep(5)
        triggered = os.path.exists(TRIGGER)
        if triggered or time.time() - last >= INTERVAL:
            if triggered:
                try:
                    os.remove(TRIGGER)
                except OSError:
                    pass
                time.sleep(20)  # let the importer finish writing before we look
            try:
                scan()
            except Exception as exc:  # keep the service alive
                print("scan error:", exc, flush=True)
            last = time.time()


if __name__ == "__main__":
    main()
