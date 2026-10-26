# Servidor de aplicação (Django REST Framework)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x arrancar.sh
# Fotografias reais dos anúncios de demonstração: se ainda não foram descarregadas para
# anuncios/fotos_reais/, tenta descarregá-las agora (precisa de internet; se falhar, o sistema
# usa imagens neutras e continua a funcionar).
RUN if [ ! -f anuncios/fotos_reais/manifesto.json ]; then python anuncios/fotos_reais/descarregar_fotos.py || true; fi

EXPOSE 8000
CMD ["./arrancar.sh"]
