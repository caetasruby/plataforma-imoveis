"""
PADRÃO DE DESENHO: OBSERVER (Observador), com os sinais do Django.

Problema: quando acontece algo importante (o administrador aprova um
anúncio, a IA gera um alerta, uma conta é bloqueada) é preciso fazer várias
coisas secundárias: gravar o log de auditoria (RNF08) e notificar o
utilizador afectado. Se a vista que faz a acção principal tivesse também de
fazer tudo isto, ficaria acoplada a módulos que não lhe dizem respeito.

Solução: a vista apenas "anuncia" o acontecimento (envia um sinal). Os
observadores (receptores) inscritos nesse sinal reagem de forma
independente. Para acrescentar uma reacção nova (por exemplo, enviar
e-mail) basta acrescentar outro receptor, sem tocar na vista.

Sujeitos (sinais):   anuncio_moderado, estado_conta_alterado,
                     parametro_alterado e post_save de AlertaFraude.
Observadores:        as funções com @receiver abaixo.
"""
from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from .configuracao import Configuracao
from .models import AlertaFraude, HistoricoInteracao, Notificacao, TipoAccao

# Sinais próprios do projecto (os "sujeitos" do padrão Observer)
anuncio_moderado = Signal()        # argumentos: anuncio, administrador, aprovado, motivo
estado_conta_alterado = Signal()   # argumentos: conta, administrador, novo_estado
parametro_alterado = Signal()      # argumentos: parametro, administrador, valor_anterior


@receiver(anuncio_moderado)
def registar_moderacao(sender, anuncio, administrador, aprovado, motivo="", **kwargs):
    decisao = "aprovado" if aprovado else "rejeitado"
    HistoricoInteracao.registar(
        administrador, TipoAccao.MODERACAO,
        f"Anúncio #{anuncio.id} «{anuncio.titulo}» {decisao}",
        anuncio=anuncio.id, decisao=decisao, motivo=motivo)


@receiver(anuncio_moderado)
def notificar_anunciante(sender, anuncio, aprovado, motivo="", **kwargs):
    if aprovado:
        mensagem = f"O seu anúncio «{anuncio.titulo}» foi aprovado e já está publicado."
    else:
        mensagem = f"O seu anúncio «{anuncio.titulo}» foi rejeitado. Motivo: {motivo}"
    Notificacao.objects.create(utilizador=anuncio.anunciante, mensagem=mensagem[:255],
                               ligacao=f"/meus-anuncios/{anuncio.id}")


@receiver(estado_conta_alterado)
def registar_estado_conta(sender, conta, administrador, novo_estado, **kwargs):
    HistoricoInteracao.registar(
        administrador, TipoAccao.UTILIZADOR,
        f"Conta de {conta.email} passou a {conta.get_estado_display()}",
        conta=conta.id, estado=novo_estado)


@receiver(parametro_alterado)
def registar_e_recarregar_parametro(sender, parametro, administrador, valor_anterior, **kwargs):
    HistoricoInteracao.registar(
        administrador, TipoAccao.PARAMETRO,
        f"Parâmetro {parametro.chave}: {valor_anterior} -> {parametro.valor}",
        parametro=parametro.chave, anterior=valor_anterior, novo=parametro.valor)
    Configuracao.instancia().recarregar()   # o Singleton passa a usar o valor novo


@receiver(post_save, sender=AlertaFraude)
def registar_alerta(sender, instance, created, **kwargs):
    if created:
        HistoricoInteracao.registar(
            None, TipoAccao.ALERTA,
            f"Alerta {instance.get_tipo_alerta_display()} ({instance.pontuacao_risco:.2f}) "
            f"no anúncio #{instance.anuncio_id}",
            anuncio=instance.anuncio_id, alerta=instance.id)
    elif instance.decidido_por_id:
        HistoricoInteracao.registar(
            instance.decidido_por, TipoAccao.ALERTA,
            f"Alerta #{instance.id} classificado como {instance.get_estado_display()}",
            anuncio=instance.anuncio_id, alerta=instance.id, estado=instance.estado)
