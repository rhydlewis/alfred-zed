#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  exit 0
fi

if command -v zed >/dev/null 2>&1; then
  exec zed "$TARGET"
else
  exec open -a "Zed" "$TARGET"
fi
