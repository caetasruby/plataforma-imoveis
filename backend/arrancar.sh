#!/bin/sh
# Arranque do servidor no Docker:
# 1. espera pela base de dados, 2. cria as tabelas, 3. carrega a demonstração
# (só na primeira vez), 4. prepara os ficheiros estáticos, 5. inicia o servidor.
set -e

echo "A aguardar pela base de dados..."
until python -c "import psycopg, os; psycopg.connect(host=os.environ['POSTGRES_HOST'], dbname=os.environ['POSTGRES_DB'], user=os.environ['POSTGRES_USER'], password=os.environ['POSTGRES_PASSWORD'], port=os.environ.get('POSTGRES_PORT', '5432')).close()" 2>/dev/null; do
  sleep 1
done

python manage.py migrate --noinput
python manage.py carregar_demo
python manage.py collectstatic --noinput -v 0

# 3 processos independentes: o servidor não guarda sessão (RNF04)
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
