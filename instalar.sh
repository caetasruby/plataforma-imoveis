#!/bin/sh
# Instalação da Casa Certa (Linux / macOS). Requisito: Docker instalado e em execução.
set -e
cd "$(dirname "$0")"

if ! docker info >/dev/null 2>&1; then
  echo "O Docker não está em execução. Instale o Docker Desktop (https://www.docker.com) e abra-o antes de continuar."
  exit 1
fi

# Se o CD trouxer as imagens já preparadas, instala sem precisar de internet
if [ -f imagens/casa-certa-imagens.tar ]; then
  echo "A carregar as imagens do CD (sem internet)..."
  docker load -i imagens/casa-certa-imagens.tar
  docker compose up -d --no-build
else
  echo "A preparar o sistema (a primeira vez demora alguns minutos e precisa de internet)..."
  docker compose up -d --build
fi

echo "A aguardar que o sistema arranque..."
i=0
until curl -s -o /dev/null http://localhost:3000/api/anuncios/; do
  i=$((i+1)); [ $i -gt 180 ] && { echo "O sistema não respondeu. Veja: docker compose logs backend"; exit 1; }
  sleep 2
done

echo ""
echo "Casa Certa pronta em http://localhost:3000"
echo "Contas de demonstração (palavra-passe Demo@2026):"
echo "  inquilino@imoveis.co.mz | agencia@imoveis.co.mz | admin@imoveis.co.mz"
(command -v xdg-open >/dev/null && xdg-open http://localhost:3000) || (command -v open >/dev/null && open http://localhost:3000) || true
