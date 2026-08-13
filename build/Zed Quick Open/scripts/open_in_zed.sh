#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  exit 0
fi

spawn() {
  ( "$@" </dev/null >/dev/null 2>&1 & disown ) &
}

if [[ "$TARGET" == "newwindow" ]]; then
  if command -v zed >/dev/null 2>&1; then
    spawn zed --new
  else
    spawn open -n -a "Zed"
  fi
  exit 0
fi

if [[ "$TARGET" == new:* ]]; then
  TARGET_PATH="${TARGET#new:}"
  if command -v zed >/dev/null 2>&1; then
    spawn zed --new "$TARGET_PATH"
  else
    spawn open -n -a "Zed" "$TARGET_PATH"
  fi
  exit 0
fi

if [[ "$TARGET" == finder:* ]]; then
  TARGET_PATH="${TARGET#finder:}"
  spawn open -R "$TARGET_PATH"
  exit 0
fi

if [[ "$TARGET" == tab:* ]]; then
  TAB_INDEX="${TARGET#tab:}"
  /usr/bin/osascript <<OSA >/dev/null 2>&1 || true
tell application "Zed" to activate
tell application "System Events"
  tell process "Zed"
    set theMenu to menu 1 of menu bar item "Window" of menu bar 1
    click menu item ${TAB_INDEX} of theMenu
  end tell
end tell
OSA
  exit 0
fi

if command -v zed >/dev/null 2>&1; then
  spawn zed "$TARGET"
else
  spawn open -a "Zed" "$TARGET"
fi
