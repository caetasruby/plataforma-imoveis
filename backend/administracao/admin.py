from django.contrib import admin

from .models import AlertaFraude, HistoricoInteracao, Notificacao, ParametroSistema

admin.site.register([AlertaFraude, HistoricoInteracao, Notificacao, ParametroSistema])
