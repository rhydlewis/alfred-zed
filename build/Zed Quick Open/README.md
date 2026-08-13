# Alfred Workflow: Zed Quick Open

This folder contains scripts for an Alfred workflow that lets you:

1. List/search **recent Zed projects**
2. Search and open a **folder** in Zed
3. Search and open a **file** in Zed
4. Open a **new empty Zed window**

## Files

- `scripts/zed_filter.py` – Script Filter backend (outputs Alfred JSON)
- `scripts/open_in_zed.sh` – Opens selected file/folder in Zed (supports modifiers/new window)

## Prereqs

- Alfred (with Powerpack for workflows)
- Zed installed
- macOS Spotlight indexing enabled (for folder/file search)
- Python 3 (`/usr/bin/python3` is fine)

---

## Build the workflow in Alfred

Create a new blank workflow, then add these objects:

## 1) Recent Zed projects

### Keyword Input
- **Keyword**: `zr`
- **Title**: `Zed Recent Projects`
- **Argument Optional**: ✅ (allow empty query)

### Script Filter (connect from Keyword)
- **Language**: `/usr/bin/python3`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/zed_filter.py recent "$1"
  ```

### Run Script (connect from Script Filter)
- **Language**: `/bin/bash`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/open_in_zed.sh "$1"
  ```

---

## 2) Open folder in Zed

### Keyword Input
- **Keyword**: `zfo`
- **Title**: `Zed Open Folder`
- **Argument Optional**: ✅

### Script Filter
- **Language**: `/usr/bin/python3`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/zed_filter.py folders "$1"
  ```

### Run Script
- **Language**: `/bin/bash`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/open_in_zed.sh "$1"
  ```

---

## 3) Open file in Zed

### Keyword Input
- **Keyword**: `zfi`
- **Title**: `Zed Open File`
- **Argument Optional**: ✅

### Script Filter
- **Language**: `/usr/bin/python3`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/zed_filter.py files "$1"
  ```

### Run Script
- **Language**: `/bin/bash`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/open_in_zed.sh "$1"
  ```

---

## 4) New empty Zed window

### Keyword Input
- **Keyword**: `zn`
- **Title**: `New Zed Window`
- **Argument Optional**: ✅

### Script Filter
- **Language**: `/usr/bin/python3`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/zed_filter.py new "$1"
  ```

### Run Script
- **Language**: `/bin/bash`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/open_in_zed.sh "$1"
  ```

---

## Notes

- Recent projects are read from:
  - `~/Library/Application Support/Zed/db/<channel>/db.sqlite` (`workspaces` table)
- `ZED_CHANNEL` workflow var controls channel (default `0-stable`, can be `0-preview` / `0-nightly`).
- `ZED_LIMIT` workflow var controls max result count (default `60`).
- Folder/file search uses `mdfind` (Spotlight), so results depend on Spotlight index freshness.
- Result modifiers:
  - `⌘↩` open in a **new** Zed window
  - `⌥↩` reveal in Finder
- In `zr`, typing an existing path (e.g. `~/code/foo`) adds a fallback item to open that path in Zed.
- If Zed CLI (`zed`) is available, it is used. Otherwise it falls back to `open -a "Zed"`.

## Optional: Pack/export

In Alfred workflow editor:
- Set a name/icon
- Use **Export...** to produce a `.alfredworkflow` file.
