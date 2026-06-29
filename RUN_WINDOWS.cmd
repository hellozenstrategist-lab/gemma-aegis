@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
set PYTHONPATH=%CD%
python -m gemma_hack.server --host 0.0.0.0 --port 8765
