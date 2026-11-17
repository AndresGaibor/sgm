#!/bin/sh
# Gancho PreToolUse de Claude Code: bloquea `git commit` sin cierre verde.
# El JSON del evento llega por la entrada estándar; `validacion.py guardia` lo interpreta.
#
# El gancho corre en CADA comando de Bash, y arrancar Python cuesta ~0.5 s. Por eso primero se
# descarta aquí, sin arrancar nada, todo lo que no sea un commit: el filtro es grueso a propósito,
# `guardia` vuelve a comprobar el comando de verdad.
set -u

entrada=$(cat)
case "$entrada" in
    *commit*) ;;
    *) exit 0 ;;
esac

raiz="${CLAUDE_PROJECT_DIR:-}"
if [ -n "$raiz" ]; then
    # En Windows, Claude puede dar una ruta nativa; el shell del gancho puede ser Git Bash o WSL.
    if command -v cygpath >/dev/null 2>&1; then
        raiz=$(cygpath -u "$raiz")
    elif command -v wslpath >/dev/null 2>&1; then
        raiz=$(wslpath -u "$raiz" 2>/dev/null || printf '%s' "$raiz")
    else
        raiz=$(printf '%s' "$raiz" | tr '\\' '/')
    fi
else
    raiz=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
fi
[ -n "$raiz" ] || exit 0
cd "$raiz" || exit 0

if [ -x ".venv/Scripts/python.exe" ]; then
    python=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
    python=".venv/bin/python"
else
    python="python"
fi

printf '%s' "$entrada" | "$python" tools/validacion.py guardia
