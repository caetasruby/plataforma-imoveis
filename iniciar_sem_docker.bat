@echo off
chcp 65001 >nul
title Kaya Justa - Arranque sem Docker
cd /d "%~dp0"
echo.
echo  Kaya Justa - arranque sem Docker (SQLite + Django + Vite)
echo  ==========================================================
echo.
rem Requisitos: Python 3.12 ou superior e Node.js 20 ou superior.
where python >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado. Instale em https://www.python.org e marque "Add to PATH".
  pause
  exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
  echo Node.js nao encontrado. Instale em https://nodejs.org
  pause
  exit /b 1
)

rem 1. Servidor: ambiente virtual e dependencias (so na primeira vez)
if not exist "backend\.venv\Scripts\python.exe" (
  echo A criar o ambiente Python...
  python -m venv backend\.venv
)
"backend\.venv\Scripts\python.exe" -c "import django, sklearn" >nul 2>&1
if errorlevel 1 (
  echo A instalar as dependencias do servidor. A primeira vez precisa de internet...
  "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
  if errorlevel 1 ( echo Falhou a instalacao do servidor. & pause & exit /b 1 )
)

rem 2. Base de dados SQLite: tabelas e demonstracao (carregar_demo so carrega se estiver vazia)
pushd backend
".venv\Scripts\python.exe" manage.py migrate --noinput
".venv\Scripts\python.exe" manage.py carregar_demo
popd

rem 3. Cliente: dependencias (so na primeira vez)
if not exist "frontend\node_modules" (
  echo A instalar as dependencias do cliente...
  pushd frontend
  call npm install --no-audit --no-fund
  popd
)

rem 4. Arrancar os dois servidores em janelas proprias
start "Kaya Justa - servidor (8000)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe manage.py runserver 8000"
start "Kaya Justa - cliente (3000)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo A aguardar que o sistema arranque...
set /a tentativas=0
:esperar
set /a tentativas+=1
if %tentativas% gtr 60 (
  echo O sistema nao respondeu. Veja as mensagens nas duas janelas abertas.
  pause
  exit /b 1
)
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://localhost:3000/api/anuncios/ -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
  timeout /t 2 >nul
  goto esperar
)
echo.
echo Kaya Justa pronta em http://localhost:3000
echo Contas de demonstracao ^(palavra-passe Demo@2026^):
echo   inquilino@imoveis.co.mz  ^|  agencia@imoveis.co.mz  ^|  admin@imoveis.co.mz
echo Para parar: feche as duas janelas do servidor e do cliente.
start http://localhost:3000
pause
