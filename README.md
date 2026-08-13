# Alfred Workflow: Zed Quick Open

This folder contains scripts for an Alfred workflow that lets you:

1. List/search **recent Zed projects**
2. Search and open a **folder** in Zed
3. Search and open a **file** in Zed

## Files

- `scripts/zed_filter.py` – Script Filter backend (outputs Alfred JSON)
- `scripts/open_in_zed.sh` – Opens selected file/folder in Zed

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
  /full/path/to/scripts/zed_filter.py recent "{query}"
  ```

### Run Script (connect from Script Filter)
- **Language**: `/bin/bash`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/open_in_zed.sh "{query}"
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
  /full/path/to/scripts/zed_filter.py folders "{query}"
  ```

### Run Script
- **Language**: `/bin/bash`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/open_in_zed.sh "{query}"
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
  /full/path/to/scripts/zed_filter.py files "{query}"
  ```

### Run Script
- **Language**: `/bin/bash`
- **with input as argv**: ✅
- **Script**:
  ```bash
  /full/path/to/scripts/open_in_zed.sh "{query}"
  ```

---

## Notes

- Recent projects are read from:
  - `~/Library/Application Support/Zed/db/0-stable/db.sqlite` (`workspaces` table)
- Folder/file search uses `mdfind` (Spotlight), so results depend on Spotlight index freshness.
- If Zed CLI (`zed`) is available, it is used. Otherwise it falls back to `open -a "Zed"`.

## Optional: Pack/export

In Alfred workflow editor:
- Set a name/icon
- Use **Export...** to produce a `.alfredworkflow` file.
