@echo off
REM Donkey Kong — lanzador para Windows
REM Requiere Python 3.13+ en el PATH.
REM Si tienes uv instalado lo usa directamente; si no, crea un venv con pip.

setlocal

where uv >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Usando uv...
    uv sync
    uv run donkeykong %*
    goto :eof
)

REM Sin uv: venv manual
if not exist ".venv\Scripts\activate.bat" (
    echo Creando entorno virtual...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -q -e .

echo Iniciando Donkey Kong...
python -m donkeykong %*
