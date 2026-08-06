#!/usr/bin/env bash
# PostToolUse hook: valida la sintaxis de archivos Python tras Edit/Write.
# Recibe por stdin el JSON del evento; sale 0 si no aplica.
set -u

payload="$(cat)"

file_path="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
' 2>/dev/null)"

case "$file_path" in
  *.py) ;;
  *) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

if ! python3 -m py_compile "$file_path" 2>/tmp/claude_hook_pyerr; then
  echo "Error de sintaxis en $file_path:" >&2
  cat /tmp/claude_hook_pyerr >&2
  exit 2
fi

exit 0
