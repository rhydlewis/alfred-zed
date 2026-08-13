#!/usr/bin/env python3
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

MAX_ITEMS = 60


def fuzzy_match(query: str, text: str) -> bool:
    if not query:
        return True
    q = query.lower().strip()
    t = text.lower()
    parts = q.split()
    return all(p in t for p in parts)


def score(query: str, path: str) -> int:
    if not query:
        return 0
    q = query.lower().strip()
    p = path.lower()
    s = 0
    if p.endswith('/' + q):
        s += 100
    if os.path.basename(p) == q:
        s += 120
    if q in os.path.basename(p).lower():
        s += 60
    if q in p:
        s += 20
    s -= len(p) // 20
    return s


def alfred_item(title, subtitle, arg, icon_type='fileicon', icon_path=None):
    item = {
        'title': title,
        'subtitle': subtitle,
        'arg': arg,
        'valid': True,
        'uid': arg,
        'icon': {'type': icon_type, 'path': icon_path or arg},
    }
    return item


def zed_db_path() -> Path:
    return Path.home() / 'Library/Application Support/Zed/db/0-stable/db.sqlite'


def recent_projects(query: str):
    db = zed_db_path()
    if not db.exists():
        return []

    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT timestamp, paths, identity_paths
        FROM workspaces
        ORDER BY datetime(timestamp) DESC
        LIMIT 300
        """
    )

    seen = set()
    ranked = []

    for ts, paths, identity_paths in cur.fetchall():
        raw = identity_paths or paths or ''
        if not raw:
            continue

        for p in raw.splitlines():
            p = p.strip()
            if not p:
                continue
            pp = Path(p).expanduser()
            if pp.is_file():
                pp = pp.parent
            p = str(pp)
            if p in seen:
                continue
            if not os.path.isdir(p):
                continue
            if not fuzzy_match(query, p):
                continue
            seen.add(p)
            ranked.append((score(query, p), ts, p))

    conn.close()

    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [p for _, _, p in ranked[:MAX_ITEMS]]


def mdfind_paths(query: str, folders: bool):
    if not query:
        return []

    safe_q = query.replace('"', '\\"')

    if folders:
        expr = f"kMDItemFSName == '*{safe_q}*'cd && kMDItemContentType == 'public.folder'"
    else:
        expr = f"kMDItemFSName == '*{safe_q}*'cd && kMDItemContentType != 'public.folder'"

    cmd = ['mdfind', '-onlyin', str(Path.home()), expr]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
    except Exception:
        return []

    paths = []
    for line in res.stdout.splitlines():
        p = line.strip()
        if not p:
            continue
        if folders and not os.path.isdir(p):
            continue
        if not folders and not os.path.isfile(p):
            continue
        if not fuzzy_match(query, p):
            continue
        paths.append(p)
        if len(paths) >= 400:
            break

    paths.sort(key=lambda p: score(query, p), reverse=True)
    return paths[:MAX_ITEMS]


def folder_search(query: str):
    if not query:
        return recent_projects('')[:MAX_ITEMS]
    return mdfind_paths(query, folders=True)


def file_search(query: str):
    return mdfind_paths(query, folders=False)


def build_items(mode: str, query: str):
    if mode == 'recent':
        paths = recent_projects(query)
        return [
            alfred_item(
                title=os.path.basename(p) or p,
                subtitle=f"Recent Zed project • {p}",
                arg=p,
            )
            for p in paths
        ]

    if mode == 'folders':
        paths = folder_search(query)
        return [
            alfred_item(
                title=os.path.basename(p) or p,
                subtitle=f"Open folder in Zed • {p}",
                arg=p,
            )
            for p in paths
        ]

    if mode == 'files':
        paths = file_search(query)
        return [
            alfred_item(
                title=os.path.basename(p) or p,
                subtitle=f"Open file in Zed • {p}",
                arg=p,
            )
            for p in paths
        ]

    return []


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'recent'
    query = sys.argv[2] if len(sys.argv) > 2 else ''

    items = build_items(mode, query)

    if not items:
        hint = {
            'recent': 'No recent Zed projects found',
            'folders': 'Type to search folders (Spotlight index)',
            'files': 'Type to search files (Spotlight index)',
        }.get(mode, 'No results')
        items = [{
            'title': hint,
            'subtitle': 'Press Enter does nothing',
            'valid': False,
        }]

    print(json.dumps({'items': items}))


if __name__ == '__main__':
    main()
