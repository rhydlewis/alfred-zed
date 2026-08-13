#!/usr/bin/env python3
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_MAX_ITEMS = 60


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


def get_max_items() -> int:
    raw = os.getenv('ZED_LIMIT', str(DEFAULT_MAX_ITEMS)).strip()
    try:
        val = int(raw)
        return max(1, min(val, 500))
    except Exception:
        return DEFAULT_MAX_ITEMS


def alfred_item(title, subtitle, arg, icon_type='fileicon', icon_path=None, mods=None):
    item = {
        'title': title,
        'subtitle': subtitle,
        'arg': arg,
        'valid': True,
        'uid': arg,
        'icon': {'type': icon_type, 'path': icon_path or arg},
    }
    if mods:
        item['mods'] = mods
    return item


def zed_db_path() -> Path:
    channel = os.getenv('ZED_CHANNEL', '0-stable').strip() or '0-stable'
    return Path.home() / f'Library/Application Support/Zed/db/{channel}/db.sqlite'


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
    return [p for _, _, p in ranked[:get_max_items()]]


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
    return paths[:get_max_items()]


def folder_search(query: str):
    if not query:
        return recent_projects('')[:get_max_items()]
    return mdfind_paths(query, folders=True)


def file_search(query: str):
    return mdfind_paths(query, folders=False)


def parse_roots() -> list[str]:
    raw = os.getenv('ZED_PROJECT_ROOTS', '~/code')
    parts = [p.strip() for p in raw.split(':') if p.strip()]
    roots = []
    for p in parts:
        ep = os.path.expanduser(p)
        if os.path.isdir(ep):
            roots.append(ep)
    return roots


def projects_cache_file() -> Path:
    return Path(tempfile.gettempdir()) / 'alfred-zed-projects-cache.json'


def scan_projects() -> list[str]:
    roots = parse_roots()
    if not roots:
        return []

    projects = set()
    maxdepth = os.getenv('ZED_PROJECT_SCAN_DEPTH', '4').strip() or '4'

    for root in roots:
        got_any = False
        try:
            res = subprocess.run(
                ['mdfind', '-onlyin', root, "kMDItemFSName == '.git' && kMDItemContentType == 'public.folder'"],
                capture_output=True,
                text=True,
                timeout=4,
            )
            for line in res.stdout.splitlines():
                git_dir = line.strip()
                if not git_dir:
                    continue
                parent = str(Path(git_dir).parent)
                if os.path.isdir(parent):
                    projects.add(parent)
                    got_any = True
        except Exception:
            pass

        if got_any:
            continue

        # Spotlight fallback: filesystem scan (slower, bounded by depth)
        try:
            res2 = subprocess.run(
                ['find', root, '-maxdepth', maxdepth, '-type', 'd', '-name', '.git'],
                capture_output=True,
                text=True,
                timeout=6,
            )
            for line in res2.stdout.splitlines():
                git_dir = line.strip()
                if not git_dir:
                    continue
                parent = str(Path(git_dir).parent)
                if os.path.isdir(parent):
                    projects.add(parent)
        except Exception:
            pass

    return sorted(projects)


def indexed_projects(query: str) -> list[str]:
    ttl = int(os.getenv('ZED_PROJECT_CACHE_TTL', '300') or '300')
    cache = projects_cache_file()
    now = int(time.time())
    roots = parse_roots()
    roots_key = '|'.join(sorted(roots))

    projects = None
    if cache.exists():
        try:
            data = json.loads(cache.read_text())
            same_roots = data.get('roots') == roots_key
            fresh = now - int(data.get('ts', 0)) <= ttl
            if same_roots and fresh:
                projects = data.get('projects', [])
        except Exception:
            projects = None

    if projects is None:
        projects = scan_projects()
        try:
            cache.write_text(json.dumps({'ts': now, 'roots': roots_key, 'projects': projects}))
        except Exception:
            pass

    if not query:
        return projects[:get_max_items()]

    ranked = []
    for p in projects:
        if fuzzy_match(query, p):
            ranked.append((score(query, p), p))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in ranked[:get_max_items()]]


def list_zed_tabs() -> list[tuple[str, int]]:
    script = r'''
    tell application "System Events"
      if not (exists process "Zed") then
        return ""
      end if
      tell process "Zed"
        set theMenu to menu 1 of menu bar item "Window" of menu bar 1
        set theItems to menu items of theMenu
        set foundSeparators to 0
        set results to {}
        set idx to 0
        repeat with mi in theItems
          set idx to idx + 1
          set t to name of mi
          if t is missing value then
            set foundSeparators to foundSeparators + 1
          else if foundSeparators >= 4 then
            set end of results to (idx as text) & ":::" & t
          end if
        end repeat
        set AppleScript's text item delimiters to "|||"
        return results as text
      end tell
    end tell
    '''
    try:
        res = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=3)
    except Exception:
        return []
    if res.returncode != 0:
        return []

    out = res.stdout.strip()
    if not out:
        return []

    tabs = []
    for part in out.split('|||'):
        if ':::' not in part:
            continue
        idx, label = part.split(':::', 1)
        try:
            tabs.append((label.strip(), int(idx.strip())))
        except Exception:
            continue
    return tabs


def filter_tabs(query: str) -> list[tuple[str, int]]:
    tabs = list_zed_tabs()
    if not query:
        return tabs[:get_max_items()]

    ranked = []
    for label, idx in tabs:
        if fuzzy_match(query, label):
            ranked.append((score(query, label), label, idx))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [(label, idx) for _, label, idx in ranked[:get_max_items()]]


def zed_mods(path: str):
    return {
        'cmd': {
            'arg': f'new:{path}',
            'subtitle': f'⌘ Open in a new Zed window • {path}',
        },
        'alt': {
            'arg': f'finder:{path}',
            'subtitle': f'⌥ Reveal in Finder • {path}',
        },
    }


def looks_like_path(query: str) -> bool:
    q = (query or '').strip()
    return q.startswith('/') or q.startswith('~/') or q.startswith('./') or q.startswith('../')


def expand_query_path(query: str) -> str:
    return os.path.abspath(os.path.expanduser(query.strip()))


def maybe_path_fallback(items, query: str, mode: str):
    if mode != 'recent':
        return items
    if not looks_like_path(query):
        return items

    try:
        candidate = expand_query_path(query)
    except Exception:
        return items

    if not os.path.exists(candidate):
        return items

    target = candidate if os.path.isdir(candidate) else str(Path(candidate).parent)
    if any(i.get('arg') == target for i in items):
        return items

    fallback = alfred_item(
        title=os.path.basename(target) or target,
        subtitle=f'Open path in Zed • {target}',
        arg=target,
        mods=zed_mods(target),
    )
    return [fallback] + items


def build_items(mode: str, query: str):
    if mode == 'recent':
        paths = recent_projects(query)
        items = [
            alfred_item(
                title=os.path.basename(p) or p,
                subtitle=f"Recent Zed project • {p}",
                arg=p,
                mods=zed_mods(p),
            )
            for p in paths
        ]
        return maybe_path_fallback(items, query, mode)

    if mode == 'folders':
        paths = folder_search(query)
        return [
            alfred_item(
                title=os.path.basename(p) or p,
                subtitle=f"Open folder in Zed • {p}",
                arg=p,
                mods=zed_mods(p),
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
                mods=zed_mods(p),
            )
            for p in paths
        ]

    if mode == 'new':
        return [
            {
                'title': 'New Zed Window',
                'subtitle': 'Open a new empty Zed window',
                'arg': 'newwindow',
                'valid': True,
                'uid': 'newwindow',
                'icon': {'path': 'icon.png'},
            }
        ]

    if mode == 'projects':
        paths = indexed_projects(query)
        return [
            alfred_item(
                title=os.path.basename(p) or p,
                subtitle=f"Indexed project • {p}",
                arg=p,
                mods=zed_mods(p),
            )
            for p in paths
        ]

    if mode == 'tabs':
        tabs = filter_tabs(query)
        if not tabs:
            return [{
                'title': 'No running Zed tabs found',
                'subtitle': 'Open Zed and grant Alfred Accessibility permission if needed',
                'valid': False,
            }]

        items = []
        for label, idx in tabs:
            if ' — ' in label:
                project, file_name = label.split(' — ', 1)
            else:
                project, file_name = label, ''
            items.append({
                'title': project,
                'subtitle': f"Switch tab • {file_name}" if file_name else 'Switch tab',
                'arg': f'tab:{idx}',
                'valid': True,
                'uid': f'tab:{idx}',
                'icon': {'path': 'icon.png'},
            })
        return items

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
            'projects': 'No indexed projects found',
            'tabs': 'No running Zed tabs found',
        }.get(mode, 'No results')
        items = [{
            'title': hint,
            'subtitle': 'Press Enter does nothing',
            'valid': False,
        }]

    print(json.dumps({'items': items}))


if __name__ == '__main__':
    main()
