@echo off
REM Prepara as imagens para gravar no CD (correr uma vez num computador com internet)
cd /d "%~dp0"
docker compose build || goto erro
docker compose pull db || goto erro
if not exist imagens mkdir imagens
docker save -o imagens\kaya-justa-imagens.tar kaya-justa-backend:1.0 kaya-justa-frontend:1.0 postgres:16-alpine || goto erro
echo Imagens guardadas em imagens\kaya-justa-imagens.tar
pause
exit /b 0
:erro
echo Ocorreu um erro.
pause
exit /b 1
