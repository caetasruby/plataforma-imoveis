"""Testes de Autenticação e Perfis: TC35 a TC38 e TC41 (UC14, UC15, UC17)."""
from rest_framework.authtoken.models import Token

from config.testes_base import PASSE, TesteBase
from contas.fabrica import FabricaUtilizador
from contas.models import Administrador, InquilinoComprador, Perfil, ProprietarioAgencia, Utilizador


class TestesConta(TesteBase):

    def dados_registo(self, **alteracoes):
        dados = {"nome": "Maria Langa", "email": "maria@exemplo.co.mz", "contacto": "84 555 1234",
                 "perfil": "INQUILINO", "palavra_passe": "Casa@Maputo1",
                 "confirmar_palavra_passe": "Casa@Maputo1"}
        dados.update(alteracoes)
        return dados

    def test_tc35_registo_valido(self):
        r = self.client.post("/api/auth/registo/", self.dados_registo())
        self.assertEqual(r.status_code, 201, r.data)
        self.assertIn("token", r.data)
        conta = Utilizador.objects.get(email="maria@exemplo.co.mz")
        self.assertEqual(conta.contacto, "845551234")
        self.assertTrue(conta.check_password("Casa@Maputo1"))

    def test_tc36_registo_invalido(self):
        casos = [
            ({"email": "inq@t.mz"}, "email"),                              # e-mail repetido
            ({"palavra_passe": "12345678", "confirmar_palavra_passe": "12345678"}, "palavra_passe"),
            ({"confirmar_palavra_passe": "Outra@123"}, "confirmar_palavra_passe"),
            ({"contacto": "21123456"}, "contacto"),                          # não é telemóvel
            ({"perfil": "ADMINISTRADOR"}, "perfil"),                         # perfil reservado
            ({"nome": "Maria"}, "nome"),                                     # falta o apelido
        ]
        for alteracao, campo in casos:
            r = self.client.post("/api/auth/registo/", self.dados_registo(**alteracao))
            self.assertEqual(r.status_code, 400, alteracao)
            self.assertIn(campo, r.data, alteracao)

    def test_tc37_iniciar_sessao(self):
        ok = self.client.post("/api/auth/entrar/", {"email": "INQ@t.mz", "palavra_passe": PASSE})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.data["utilizador"]["perfil"], "INQUILINO")
        errado = self.client.post("/api/auth/entrar/", {"email": "inq@t.mz", "palavra_passe": "errada"})
        self.assertEqual(errado.status_code, 400)
        self.assertIn("incorrectos", str(errado.data))

    def test_tc38_terminar_sessao(self):
        token = self.client.post("/api/auth/entrar/", {"email": "inq@t.mz", "palavra_passe": PASSE}).data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(self.client.post("/api/auth/sair/").status_code, 204)
        self.assertFalse(Token.objects.filter(key=token).exists())
        self.assertEqual(self.client.get("/api/auth/perfil/").status_code, 401)

    def test_tc41_gerir_perfil(self):
        self.entrar(self.dono)
        r = self.client.patch("/api/auth/perfil/", {"nome": "Dono Actualizado", "contacto": "+258821112233",
                                                     "nome_agencia": "Casas do Sol"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["contacto"], "+258821112233")
        invalido = self.client.patch("/api/auth/perfil/", {"contacto": "123"})
        self.assertEqual(invalido.status_code, 400)
        errada = self.client.post("/api/auth/palavra-passe/", {"actual": "x", "nova": "Nova@Senha9"})
        self.assertEqual(errada.status_code, 400)
        certa = self.client.post("/api/auth/palavra-passe/", {"actual": PASSE, "nova": "Nova@Senha9"})
        self.assertEqual(certa.status_code, 200)


class TestesFabrica(TesteBase):
    """Padrão Factory: cada perfil cria a classe certa do diagrama de classes."""

    def test_fabrica_cria_classe_de_cada_perfil(self):
        a = FabricaUtilizador.criar(Perfil.ADMINISTRADOR, "a2@t.mz", PASSE, "Novo Admin")
        p = FabricaUtilizador.criar(Perfil.PROPRIETARIO, "p2@t.mz", PASSE, "Novo Dono")
        i = FabricaUtilizador.criar(Perfil.INQUILINO, "i2@t.mz", PASSE, "Novo Inquilino")
        self.assertIsInstance(a, Administrador)
        self.assertTrue(a.is_staff)
        self.assertIsInstance(p, ProprietarioAgencia)
        self.assertIsInstance(i, InquilinoComprador)
        self.assertFalse(i.is_staff)
        self.assertEqual(InquilinoComprador.objects.filter(email="i2@t.mz").count(), 1)
        self.assertEqual(ProprietarioAgencia.objects.filter(email="i2@t.mz").count(), 0)
