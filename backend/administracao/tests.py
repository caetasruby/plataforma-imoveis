"""
Testes do Administrador (TC18 a TC27), dos parâmetros (TC39, TC40) e dos
requisitos não funcionais verificáveis no servidor (TC28 a TC30, TC33, TC34).
"""
import time
from datetime import timedelta

from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from administracao.configuracao import Configuracao
from administracao.models import AlertaFraude, EstadoAlerta, HistoricoInteracao, Notificacao, TipoAccao
from anuncios.models import Anuncio, EstadoAnuncio
from config.testes_base import PASSE, TesteBase, imagem_teste
from contas.models import EstadoConta


class TestesModeracao(TesteBase):

    def setUp(self):
        super().setUp()
        self.pendente = self.criar_publicado(titulo="Pendente de teste")
        self.pendente.estado = EstadoAnuncio.PENDENTE
        self.pendente.pontuacao_risco = 0.7
        self.pendente.save()
        AlertaFraude.objects.create(anuncio=self.pendente, tipo_alerta="TEXTO_SUSPEITO",
                                    pontuacao_risco=0.7, justificacao="x", gravidade="MEDIA")
        self.entrar(self.admin)

    def test_tc18_fila_de_moderacao_com_alertas(self):
        r = self.client.get("/api/admin/moderacao/")
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["alertas"][0]["tipo_alerta"], "TEXTO_SUSPEITO")

    def test_tc19_aprovar(self):
        r = self.client.post(f"/api/admin/moderacao/{self.pendente.id}/aprovar/")
        self.assertEqual(r.status_code, 200)
        self.pendente.refresh_from_db()
        self.assertEqual(self.pendente.estado, EstadoAnuncio.PUBLICADO)
        self.assertTrue(Notificacao.objects.filter(utilizador=self.dono, mensagem__contains="aprovado").exists())
        self.sair()
        ids = [a["id"] for a in self.client.get("/api/anuncios/").data["results"]]
        self.assertIn(self.pendente.id, ids)

    def test_tc20_rejeitar_com_motivo(self):
        sem_motivo = self.client.post(f"/api/admin/moderacao/{self.pendente.id}/rejeitar/", {"motivo": ""})
        self.assertEqual(sem_motivo.status_code, 400)
        r = self.client.post(f"/api/admin/moderacao/{self.pendente.id}/rejeitar/",
                             {"motivo": "Fotografias não correspondem ao imóvel."})
        self.assertEqual(r.status_code, 200)
        self.pendente.refresh_from_db()
        self.assertEqual(self.pendente.estado, EstadoAnuncio.REJEITADO)
        self.assertTrue(Notificacao.objects.filter(utilizador=self.dono, mensagem__contains="Motivo").exists())

    def test_aprovar_anuncio_ja_publicado_e_recusado(self):
        publicado = self.criar_publicado()
        r = self.client.post(f"/api/admin/moderacao/{publicado.id}/aprovar/")
        self.assertEqual(r.status_code, 400)


class TestesUtilizadores(TesteBase):

    def setUp(self):
        super().setUp()
        self.entrar(self.admin)

    def test_tc21_bloquear_conta(self):
        Token.objects.create(user=self.inquilino)
        r = self.client.post(f"/api/admin/utilizadores/{self.inquilino.id}/bloquear/")
        self.assertEqual(r.status_code, 200)
        self.inquilino.refresh_from_db()
        self.assertEqual(self.inquilino.estado, EstadoConta.BLOQUEADO)
        self.assertFalse(Token.objects.filter(user=self.inquilino).exists())
        self.sair()
        entrar = self.client.post("/api/auth/entrar/", {"email": "inq@t.mz", "palavra_passe": PASSE})
        self.assertEqual(entrar.status_code, 400)
        self.assertIn("bloqueada", str(entrar.data))
        self.assertTrue(HistoricoInteracao.objects.filter(tipo_accao=TipoAccao.UTILIZADOR).exists())

    def test_tc22_reactivar_conta(self):
        self.inquilino.mudar_estado(EstadoConta.DESACTIVADO)
        r = self.client.post(f"/api/admin/utilizadores/{self.inquilino.id}/reactivar/")
        self.assertEqual(r.status_code, 200)
        self.inquilino.refresh_from_db()
        self.assertEqual(self.inquilino.estado, EstadoConta.ACTIVO)

    def test_tc23_transicao_nao_prevista(self):
        self.inquilino.mudar_estado(EstadoConta.BLOQUEADO)
        r = self.client.post(f"/api/admin/utilizadores/{self.inquilino.id}/desactivar/")
        self.assertEqual(r.status_code, 400)
        self.inquilino.refresh_from_db()
        self.assertEqual(self.inquilino.estado, EstadoConta.BLOQUEADO)

    def test_admin_nao_altera_a_propria_conta(self):
        r = self.client.post(f"/api/admin/utilizadores/{self.admin.id}/bloquear/")
        self.assertEqual(r.status_code, 400)


class TestesAlertas(TesteBase):

    def setUp(self):
        super().setUp()
        a = self.criar_publicado()
        self.alta = AlertaFraude.objects.create(anuncio=a, tipo_alerta="PRECO_ATIPICO",
                                                pontuacao_risco=0.9, justificacao="x", gravidade="ALTA")
        self.media = AlertaFraude.objects.create(anuncio=a, tipo_alerta="TEXTO_SUSPEITO",
                                                 pontuacao_risco=0.65, justificacao="y", gravidade="MEDIA")
        self.entrar(self.admin)

    def test_tc24_filtrar_e_ordenar_alertas(self):
        r = self.client.get("/api/admin/alertas/", {"gravidade": "ALTA"})
        self.assertEqual([x["id"] for x in r.data["results"]], [self.alta.id])
        r = self.client.get("/api/admin/alertas/", {"tipo_alerta": "TEXTO_SUSPEITO"})
        self.assertEqual(r.data["count"], 1)
        r = self.client.get("/api/admin/alertas/", {"ordenar": "-pontuacao_risco"})
        self.assertEqual(r.data["results"][0]["id"], self.alta.id)
        hoje = timezone.localdate().isoformat()
        self.assertEqual(self.client.get("/api/admin/alertas/", {"inicio": hoje}).data["count"], 2)

    def test_tc25_classificar_alertas(self):
        r1 = self.client.post(f"/api/admin/alertas/{self.alta.id}/classificar/", {"decisao": "RESOLVIDO"})
        r2 = self.client.post(f"/api/admin/alertas/{self.media.id}/classificar/", {"decisao": "FALSO_POSITIVO"})
        self.assertEqual((r1.status_code, r2.status_code), (200, 200))
        self.alta.refresh_from_db()
        self.media.refresh_from_db()
        self.assertEqual(self.alta.estado, EstadoAlerta.RESOLVIDO)
        self.assertEqual(self.media.estado, EstadoAlerta.FALSO_POSITIVO)
        self.assertEqual(self.alta.decidido_por, self.admin)
        # Um alerta resolvido não pode voltar atrás
        r3 = self.client.post(f"/api/admin/alertas/{self.alta.id}/classificar/", {"decisao": "FALSO_POSITIVO"})
        self.assertEqual(r3.status_code, 400)

    def test_escalamento_apos_24_horas(self):
        AlertaFraude.objects.filter(id=self.media.id).update(data_criacao=timezone.now() - timedelta(hours=30))
        self.client.get("/api/admin/alertas/")
        self.media.refresh_from_db()
        self.assertEqual(self.media.estado, EstadoAlerta.ESCALADO)


class TestesIndicadoresEPermissoes(TesteBase):

    def test_tc26_indicadores_e_exportacao(self):
        self.criar_publicado()
        self.entrar(self.admin)
        hoje = timezone.localdate().isoformat()
        r = self.client.get("/api/admin/indicadores/", {"inicio": hoje, "fim": hoje})
        self.assertEqual(r.data["periodo"], {"inicio": hoje, "fim": hoje})
        self.assertEqual(r.data["totais"]["anuncios_publicados"], 1)
        self.assertIn("tempo_medio_moderacao_horas", r.data["totais"])
        self.assertIn("publicados", r.data["serie_diaria"][0])
        csv = self.client.get("/api/admin/indicadores/exportar/", {"inicio": hoje, "fim": hoje})
        self.assertEqual(csv.status_code, 200)
        self.assertIn("text/csv", csv["Content-Type"])
        self.assertIn("Anúncios publicados", csv.content.decode("utf-8-sig"))

    def test_tc27_nao_administrador_recusado(self):
        rotas = ["/api/admin/moderacao/", "/api/admin/utilizadores/", "/api/admin/alertas/",
                 "/api/admin/indicadores/", "/api/admin/parametros/", "/api/admin/registos/"]
        for utilizador in (self.inquilino, self.dono, None):
            self.entrar(utilizador) if utilizador else self.sair()
            for rota in rotas:
                self.assertIn(self.client.get(rota).status_code, (401, 403), rota)


class TestesParametros(TesteBase):

    def setUp(self):
        super().setUp()
        self.entrar(self.admin)
        self.limiar = self.client.get("/api/admin/parametros/").data
        self.limiar = next(p for p in self.limiar if p["chave"] == "limiar_risco_fraude")

    def tearDown(self):
        Configuracao.instancia().recarregar()

    def test_tc39_alterar_parametro(self):
        r = self.client.patch(f"/api/admin/parametros/{self.limiar['id']}/", {"valor": "0,75"})
        self.assertEqual(r.status_code, 200, r.data)
        self.assertEqual(r.data["valor"], "0.75")
        self.assertEqual(Configuracao.instancia().obter("limiar_risco_fraude"), 0.75)
        self.assertTrue(HistoricoInteracao.objects.filter(tipo_accao=TipoAccao.PARAMETRO).exists())

    def test_tc40_valor_fora_dos_limites(self):
        for valor in ("2", "abc", ""):
            r = self.client.patch(f"/api/admin/parametros/{self.limiar['id']}/", {"valor": valor})
            self.assertEqual(r.status_code, 400, valor)
        self.assertEqual(Configuracao.instancia().obter("limiar_risco_fraude"), 0.6)


class TestesNaoFuncionais(TesteBase):

    def test_tc28_estimativa_e_alertas_em_menos_de_3_segundos(self):
        self.criar_mercado(25)
        self.entrar(self.dono)
        tempos = []
        for i in range(30):
            inicio = time.perf_counter()
            r = self.client.post("/api/meus-anuncios/",
                                 self.dados_formulario(preco=str(90000 + i * 1000),
                                                       imagens=[imagem_teste(f"{i}.jpg")]),
                                 format="multipart")
            tempos.append(time.perf_counter() - inicio)
            self.assertEqual(r.status_code, 201)
        self.assertLess(max(tempos), 3.0, f"Tempo máximo: {max(tempos):.2f}s")

    def test_tc29_verificacao_de_imagem_em_menos_de_5_segundos(self):
        from ia.imagens import calcular_hash
        grande = imagem_teste("grande.jpg", tamanho=(4000, 3000))
        inicio = time.perf_counter()
        calcular_hash(grande)
        self.assertLess(time.perf_counter() - inicio, 5.0)

    def test_tc30_servidor_sem_estado(self):
        """Dois clientes diferentes (como duas instâncias) com o mesmo token."""
        r = self.client.post("/api/auth/entrar/", {"email": "inq@t.mz", "palavra_passe": PASSE})
        token = r.data["token"]
        for _ in range(2):
            outro = APIClient()
            outro.credentials(HTTP_AUTHORIZATION=f"Token {token}")
            self.assertEqual(outro.get("/api/auth/perfil/").status_code, 200)

    def test_tc33_logs_de_moderacao_e_alertas(self):
        a = self.criar_publicado()
        a.estado = EstadoAnuncio.PENDENTE
        a.save()
        AlertaFraude.objects.create(anuncio=a, tipo_alerta="ANOMALIA", pontuacao_risco=0.7,
                                    justificacao="z", gravidade="MEDIA")
        self.entrar(self.admin)
        self.client.post(f"/api/admin/moderacao/{a.id}/aprovar/")
        registos = self.client.get("/api/admin/registos/").data["results"]
        tipos = {r["tipo_accao"] for r in registos}
        self.assertTrue({"MODERACAO", "ALERTA"} <= tipos)
        moderacao = next(r for r in registos if r["tipo_accao"] == "MODERACAO")
        self.assertEqual(moderacao["utilizador_nome"], "Admin Teste")
        self.assertIn("aprovado", moderacao["descricao"])
        self.assertGreaterEqual(Configuracao.instancia().obter("retencao_logs_meses"), 12)

    def test_tc34_limite_de_pedidos_ao_mapa(self):
        from unittest import mock

        from django.core.cache import cache
        from rest_framework.throttling import ScopedRateThrottle
        cache.clear()
        a = self.criar_publicado()
        # Limite reduzido a 3 pedidos por minuto só para este teste
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"mapa": "3/min"}):
            codigos = [self.client.get(f"/api/anuncios/{a.id}/mapa/").status_code for _ in range(5)]
        self.assertEqual(codigos[:3], [200, 200, 200])
        self.assertEqual(codigos[3], 429)
