#!/usr/bin/env bash
# Hook PostToolUse (Edit|Write): valida sintaxis de archivos Python editados.
# Recibe por stdin el JSON del evento y compila el archivo si es .py.
set -euo pipefail

file_path=$(python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
' 2>/dev/null || true)

if [[ "$file_path" == *.py && -f "$file_path" ]]; then
    if ! python3 -m py_compile "$file_path" 2>/tmp/py_compile_err.txt; then
        echo "Error de sintaxis en $file_path:" >&2
        cat /tmp/py_compile_err.txt >&2
        exit 2
    fi
fi

exit 0
