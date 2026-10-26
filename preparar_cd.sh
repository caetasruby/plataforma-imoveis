#!/bin/sh
# Prepara as imagens para gravar no CD (correr uma vez num computador com internet).
# Depois, o instalar.sh instala sem precisar de internet.
set -e
cd "$(dirname "$0")"
docker compose build
docker compose pull db
mkdir -p imagens
docker save -o imagens/kaya-justa-imagens.tar kaya-justa-backend:1.0 kaya-justa-frontend:1.0 postgres:16-alpine
echo "Imagens guardadas em imagens/kaya-justa-imagens.tar"
