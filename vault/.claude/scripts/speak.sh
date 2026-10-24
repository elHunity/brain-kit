#!/usr/bin/env bash
# Hook entry for speak.py. Uses the voice environment made by the installer; never fails the hook.
dir="$(cd "$(dirname "$0")" && pwd)"
py="$HOME/.secondbrain-venv/Scripts/python.exe"
[ -x "$py" ] || py="$HOME/.secondbrain-venv/bin/python"
[ -x "$py" ] || exit 0
"$py" -I "$dir/speak.py" "$@" || true
exit 0
