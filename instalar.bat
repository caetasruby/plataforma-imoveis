@echo off
chcp 65001 >nul
title Kaya Justa - Instalacao
cd /d "%~dp0"
echo.
echo  Kaya Justa - Plataforma Inteligente de Apoio a Decisao
echo  ======================================================
echo.
docker info >nul 2>&1
if errorlevel 1 (
  echo O Docker nao esta em execucao.
  echo Instale o Docker Desktop ^(https://www.docker.com^), abra-o e volte a executar este ficheiro.
  pause
  exit /b 1
)
if exist "imagens\kaya-justa-imagens.tar" (
  echo A carregar as imagens do CD ^(sem internet^)...
  docker load -i "imagens\kaya-justa-imagens.tar"
  docker compose up -d --no-build
) else (
  echo A preparar o sistema. A primeira vez demora alguns minutos e precisa de internet...
  docker compose up -d --build
)
if errorlevel 1 (
  echo Ocorreu um erro. Veja as mensagens acima.
  pause
  exit /b 1
)
echo A aguardar que o sistema arranque...
set /a tentativas=0
:esperar
set /a tentativas+=1
if %tentativas% gtr 180 (
  echo O sistema nao respondeu. Execute: docker compose logs backend
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
start http://localhost:3000
pause
