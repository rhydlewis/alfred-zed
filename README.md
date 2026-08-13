# Alfred Workflow: Zed Quick Open

This folder contains scripts for an Alfred workflow that lets you:

1. List/search **recent Zed projects**
2. Search and open a **folder** in Zed
3. Search and open a **file** in Zed
4. Open a **new empty Zed window**
5. Search **indexed projects** from configured roots
6. List and switch **currently open Zed tabs/windows**

## Files

- `scripts/zed_filter.py` – Script Filter backend (outputs Alfred JSON)
- `scripts/open_in_zed.sh` – Opens selected file/folder in Zed (supports modifiers/new window/tab switching)

## Prereqs

- Alfred (with Powerpack for workflows)
- Zed installed
- macOS Spotlight indexing enabled (for folder/file search and fast project scan)
- Python 3 (`/usr/bin/python3` is fine)
- For `zt` tab switching: Alfred needs Accessibility permission in macOS settings

---

## Keywords

- `zr` → recent projects
- `zfo` → open folder in Zed
- `zfi` → open file in Zed
- `zn` → new empty Zed window
- `zp` → indexed projects (from `ZED_PROJECT_ROOTS`)
- `zt` → switch running Zed tabs/windows

---

## Notes

- Recent projects are read from:
  - `~/Library/Application Support/Zed/db/<channel>/db.sqlite` (`workspaces` table)
- `ZED_CHANNEL` workflow var controls channel (default `0-stable`, can be `0-preview` / `0-nightly`).
- `ZED_LIMIT` workflow var controls max result count (default `60`).
- Folder/file search uses `mdfind` (Spotlight), so results depend on Spotlight index freshness.
- Result modifiers on path items:
  - `⌘↩` open in a **new** Zed window
  - `⌥↩` reveal in Finder
- In `zr`, typing an existing path (e.g. `~/code/foo`) adds a fallback item to open that path in Zed.

### Indexed projects (`zp`)

- `ZED_PROJECT_ROOTS`: colon-separated roots to scan for git repos (default `~/code`)
  - example: `~/code:~/work:~/src`
- `ZED_PROJECT_CACHE_TTL`: cache TTL in seconds (default `300`)
- `ZED_PROJECT_SCAN_DEPTH`: fallback `find` max depth if Spotlight misses results (default `4`)

### Running tabs (`zt`)

- Uses AppleScript/System Events to read Zed’s **Window** menu and switch to selected tab.
- If no tabs appear, ensure:
  - Zed is running
  - Alfred has Accessibility permission

- If Zed CLI (`zed`) is available, it is used for open actions. Otherwise it falls back to `open -a "Zed"`.

## Optional: Pack/export

In Alfred workflow editor:
- Set a name/icon
- Use **Export...** to produce a `.alfredworkflow` file.
