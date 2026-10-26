"""
Testes do Inquilino/Comprador (TC01 a TC10), do Proprietário/Agência
(TC11 a TC17) e dos favoritos (TC42). Os nomes seguem o plano de testes.
"""
from django.core.files.uploadedfile import SimpleUploadedFile

from administracao.models import AlertaFraude, EstadoAlerta, HistoricoInteracao, TipoAccao
from anuncios.models import Anuncio, EstadoAnuncio, ImagemImovel
from config.testes_base import TesteBase, imagem_teste


class TestesInquilino(TesteBase):

    def test_tc01_pesquisa_com_filtros(self):
        self.criar_publicado(bairro="Polana Cimento", divisoes=3, preco=90000)
        self.criar_publicado(bairro="Polana Cimento", divisoes=1, preco=40000)
        self.criar_publicado(bairro="Fomento", cidade="MATOLA", divisoes=3, preco=50000)
        nao_publicado = self.criar_publicado(divisoes=3, preco=80000)
        nao_publicado.estado = EstadoAnuncio.PENDENTE
        nao_publicado.save()

        r = self.client.get("/api/anuncios/", {"cidade": "MAPUTO", "tipo": "APARTAMENTO",
                                               "preco_min": 50000, "preco_max": 100000,
                                               "divisoes_min": 2})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(float(r.data["results"][0]["preco"]), 90000)

    def test_tc01b_apenas_preco_justo(self):
        """O filtro «Apenas com preço justo» só devolve anúncios dentro do intervalo estimado."""
        dentro = self.criar_publicado(preco=60000)
        fora = self.criar_publicado(preco=95000)
        for a in (dentro, fora):
            Anuncio.objects.filter(id=a.id).update(preco_justo=60000, preco_justo_min=50000,
                                                   preco_justo_max=70000)
        r = self.client.get("/api/anuncios/", {"apenas_preco_justo": "true"})
        self.assertEqual([x["id"] for x in r.data["results"]], [dentro.id])
        self.assertEqual(self.client.get("/api/anuncios/").data["count"], 2)

    def test_tc02_pesquisa_sem_resultados(self):
        self.criar_publicado()
        r = self.client.get("/api/anuncios/", {"cidade": "BEIRA", "tipo": "TERRENO"})
        self.assertEqual(r.data["count"], 0)

    def test_tc03_ordenacao(self):
        for preco in (70000, 30000, 50000):
            self.criar_publicado(preco=preco)
        crescente = self.client.get("/api/anuncios/", {"ordenar": "preco"}).data["results"]
        self.assertEqual([float(a["preco"]) for a in crescente], [30000, 50000, 70000])
        decrescente = self.client.get("/api/anuncios/", {"ordenar": "-preco"}).data["results"]
        self.assertEqual(float(decrescente[0]["preco"]), 70000)
        por_data = self.client.get("/api/anuncios/", {"ordenar": "data"})
        self.assertEqual(por_data.status_code, 200)

    def test_tc04_preco_justo_no_detalhe(self):
        a = self.criar_publicado(preco=60000, preco_justo=50000)
        a.preco_justo_min, a.preco_justo_max = 42000, 58000
        a.save()
        r = self.client.get(f"/api/anuncios/{a.id}/")
        self.assertEqual(float(r.data["preco_justo"]), 50000)
        self.assertEqual(r.data["diferenca_percentual"], 20.0)
        self.assertEqual(float(r.data["preco_justo_min"]), 42000)
        self.assertEqual(float(r.data["preco_justo_max"]), 58000)

    def test_tc05_anuncio_sinalizado_mostra_alerta(self):
        a = self.criar_publicado()
        AlertaFraude.objects.create(anuncio=a, tipo_alerta="TEXTO_SUSPEITO", pontuacao_risco=0.7,
                                    justificacao="Pede pagamento antecipado.", gravidade="MEDIA")
        r = self.client.get(f"/api/anuncios/{a.id}/")
        self.assertTrue(r.data["tem_alerta"])
        self.assertEqual(r.data["alertas"][0]["justificacao"], "Pede pagamento antecipado.")

    def test_tc06_sem_alerta_ou_falso_positivo(self):
        limpo = self.criar_publicado()
        self.assertFalse(self.client.get(f"/api/anuncios/{limpo.id}/").data["tem_alerta"])
        fp = self.criar_publicado()
        AlertaFraude.objects.create(anuncio=fp, tipo_alerta="PRECO_ATIPICO", pontuacao_risco=0.7,
                                    justificacao="x", gravidade="MEDIA",
                                    estado=EstadoAlerta.FALSO_POSITIVO)
        r = self.client.get(f"/api/anuncios/{fp.id}/")
        self.assertFalse(r.data["tem_alerta"])
        self.assertEqual(r.data["alertas"], [])

    def test_tc07_mapa_com_distancias(self):
        a = self.criar_publicado()
        r = self.client.get(f"/api/anuncios/{a.id}/mapa/")
        self.assertEqual(r.status_code, 200)
        self.assertAlmostEqual(r.data["latitude"], -25.965)
        categorias = {p["categoria"] for p in r.data["pontos_interesse"]}
        self.assertEqual(categorias, {"Escola", "Mercado"})
        self.assertTrue(all(p["distancia_km"] > 0 for p in r.data["pontos_interesse"]))

    def test_tc08_endereco_textual_disponivel(self):
        """Parte do servidor do TC08: a resposta traz sempre o endereço textual,
        que o cliente mostra quando o serviço de mapas falha."""
        a = self.criar_publicado()
        r = self.client.get(f"/api/anuncios/{a.id}/mapa/")
        self.assertIn("Polana Cimento", r.data["endereco"])

    def test_tc09_recomendacoes_com_historico(self):
        self.criar_mercado(10)
        for i in range(6):
            self.criar_publicado(bairro="Machava", cidade="MATOLA", tipo="MORADIA", preco=30000 + i)
        visto = self.criar_publicado(bairro="Machava", cidade="MATOLA", tipo="MORADIA", preco=31000)
        self.entrar(self.inquilino)
        self.client.get(f"/api/anuncios/{visto.id}/")   # gera histórico (CT05)
        r = self.client.get("/api/recomendacoes/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data)
        self.assertTrue(all(a["imovel"]["bairro"] == "Machava" for a in r.data[:3]))
        self.assertIn("motivo", r.data[0])

    def test_tc10_assistente_responde_e_segue_tema(self):
        for pergunta, tema in (("O que é o DUAT?", "duat"), ("Quanto é a caução?", "caucao"),
                               ("Quanto pago de SISA?", "sisa")):
            r = self.client.post("/api/assistente/", {"pergunta": pergunta})
            self.assertEqual(r.data["topico"], tema)
        # Pergunta complementar sem palavras do tema: usa o tema anterior
        r = self.client.post("/api/assistente/", {"pergunta": "E quem paga?",
                                                  "topico_anterior": "sisa"})
        self.assertEqual(r.data["topico"], "sisa")
        self.assertIn("comprador", r.data["resposta"])
        vazio = self.client.post("/api/assistente/", {"pergunta": ""})
        self.assertEqual(vazio.status_code, 400)


class TestesProprietario(TesteBase):

    def setUp(self):
        super().setUp()
        self.criar_mercado(20)
        self.entrar(self.dono)

    def test_tc11_publicar_anuncio_valido(self):
        r = self.client.post("/api/meus-anuncios/", self.dados_formulario(), format="multipart")
        self.assertEqual(r.status_code, 201, r.data)
        anuncio = Anuncio.objects.get(id=r.data["id"])
        self.assertEqual(anuncio.estado, EstadoAnuncio.PENDENTE)
        self.assertIsNotNone(anuncio.preco_justo)
        self.assertIn("pendente de moderação", r.data["mensagem"])
        self.assertEqual(anuncio.imagens.count(), 1)

    def test_tc12_dados_em_falta_ou_ficheiro_invalido(self):
        antes = Anuncio.objects.count()
        # Campos obrigatórios em falta
        r = self.client.post("/api/meus-anuncios/", self.dados_formulario(titulo="", bairro=""),
                             format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("titulo", r.data)
        self.assertIn("bairro", r.data)
        # Regras entre campos: preço fora dos limites e nenhuma fotografia
        r = self.client.post("/api/meus-anuncios/", self.dados_formulario(preco="10", imagens=[]),
                             format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("preco", r.data)
        self.assertIn("imagens", r.data)
        invalido = SimpleUploadedFile("x.jpg", b"texto simples", content_type="image/jpeg")
        r = self.client.post("/api/meus-anuncios/", self.dados_formulario(imagens=[invalido]),
                             format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("imagens", r.data)
        self.assertEqual(Anuncio.objects.count(), antes)

    def test_tc13_preco_atipico_gera_alerta(self):
        r = self.client.post("/api/meus-anuncios/", self.dados_formulario(preco="900000"),
                             format="multipart")
        anuncio = Anuncio.objects.get(id=r.data["id"])
        self.assertGreaterEqual(anuncio.pontuacao_risco, 0.6)
        self.assertTrue(anuncio.alertas.filter(tipo_alerta="PRECO_ATIPICO").exists())

    def test_tc14_imagem_duplicada_gera_alerta(self):
        existente = Anuncio.objects.first().imagens.first()
        existente.ficheiro.open("rb")
        copia = SimpleUploadedFile("copia.jpg", existente.ficheiro.read(), content_type="image/jpeg")
        r = self.client.post("/api/meus-anuncios/", self.dados_formulario(imagens=[copia]),
                             format="multipart")
        anuncio = Anuncio.objects.get(id=r.data["id"])
        self.assertTrue(anuncio.alertas.filter(tipo_alerta="IMAGEM_DUPLICADA").exists())
        self.assertTrue(ImagemImovel.objects.get(anuncio=anuncio).eh_duplicada)

    def test_tc15_editar_reanalisa_e_volta_a_moderacao(self):
        a = self.criar_publicado(dono=self.dono, preco=100000)
        dados = self.dados_formulario(preco="105000", descricao="Nova descrição do apartamento "
                                      "com mais pormenores sobre a cozinha.", imagens=[])
        r = self.client.put(f"/api/meus-anuncios/{a.id}/", dados, format="multipart")
        self.assertEqual(r.status_code, 200, r.data)
        a.refresh_from_db()
        self.assertEqual(a.estado, EstadoAnuncio.PENDENTE)
        self.assertEqual(float(a.preco), 105000)
        self.assertIsNotNone(a.preco_justo)

    def test_tc16_remover_anuncio_proprio(self):
        a = self.criar_publicado(dono=self.dono)
        r = self.client.delete(f"/api/meus-anuncios/{a.id}/")
        self.assertEqual(r.status_code, 204)
        a.refresh_from_db()
        self.assertEqual(a.estado, EstadoAnuncio.REMOVIDO)
        ids = [x["id"] for x in self.client.get("/api/anuncios/", {"tamanho": 100}).data["results"]]
        self.assertNotIn(a.id, ids)

    def test_tc17_remover_anuncio_de_outro_titular(self):
        alheio = self.criar_publicado(dono=self.outro_dono)
        r = self.client.delete(f"/api/meus-anuncios/{alheio.id}/")
        self.assertIn(r.status_code, (403, 404))
        alheio.refresh_from_db()
        self.assertEqual(alheio.estado, EstadoAnuncio.PUBLICADO)

    def test_inquilino_nao_pode_publicar(self):
        self.entrar(self.inquilino)
        r = self.client.post("/api/meus-anuncios/", self.dados_formulario(), format="multipart")
        self.assertEqual(r.status_code, 403)


class TestesFavoritos(TesteBase):

    def test_tc42_guardar_e_retirar_favorito(self):
        a = self.criar_publicado()
        self.entrar(self.inquilino)
        self.assertEqual(self.client.post("/api/favoritos/", {"anuncio": a.id}).status_code, 201)
        lista = self.client.get("/api/favoritos/").data
        self.assertEqual(lista[0]["anuncio"]["id"], a.id)
        self.assertTrue(HistoricoInteracao.objects.filter(tipo_accao=TipoAccao.FAVORITO).exists())
        self.assertEqual(self.client.delete(f"/api/favoritos/{a.id}/").status_code, 204)
        self.assertEqual(self.client.get("/api/favoritos/").data, [])
        # Um proprietário não tem favoritos
        self.entrar(self.dono)
        self.assertEqual(self.client.post("/api/favoritos/", {"anuncio": a.id}).status_code, 403)
