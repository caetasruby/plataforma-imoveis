@echo off
cd /d "%~dp0"
docker compose stop
echo Sistema parado. Os dados ficam guardados.
pause
