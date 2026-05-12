#!/usr/bin/env bash
# Donkey Kong — lanzador para Linux/macOS
# Requiere Python 3.13+. Usa uv si está disponible.
set -euo pipefail

if command -v uv &>/dev/null; then
    echo "Usando uv..."
    uv sync
    exec uv run donkeykong "$@"
fi

# Sin uv: venv manual
if [ ! -f ".venv/bin/activate" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
echo "Instalando dependencias..."
pip install -q -e .
echo "Iniciando Donkey Kong..."
exec python -m donkeykong "$@"
