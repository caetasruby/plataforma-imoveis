"""
Assistente virtual com um modelo de linguagem local (Ollama), UC09.

O assistente por regras (assistente.py) continua a ser a base:
  1. As regras identificam o tema da pergunta (DUAT, caução, SISA...) e as
     sugestões de seguimento, como antes (TC10).
  2. O texto desse tema é dado ao modelo como informação de referência, para
     que os factos legais e os impostos venham das regras e não da memória
     do modelo.
  3. O modelo escreve a resposta em linguagem natural, com o contexto das
     últimas mensagens da conversa.
  4. Se o Ollama não estiver a correr, demorar demasiado ou falhar, devolve-se
     a resposta das regras: o assistente nunca fica sem resposta.

Configuração (variáveis de ambiente, ver settings.py):
  ASSISTENTE_MOTOR  auto (usa o Ollama se estiver disponível) | regras
  OLLAMA_URL        por omissão http://127.0.0.1:11434
  OLLAMA_MODELO     por omissão qwen2.5:3b
"""
import json
import urllib.error
import urllib.request

from django.conf import settings

from . import assistente
from .risco import sem_acentos

INSTRUCOES = (
    "És o assistente virtual da Kaya Justa, uma plataforma de arrendamento e compra de imóveis "
    "em Moçambique (Maputo, Matola e Beira). Respondes sempre em português de Moçambique, "
    "tratando o utilizador por «você». Responde em 2 a 4 frases (no máximo 120 palavras), "
    "com os detalhes úteis da informação de referência (valores, percentagens, documentos, "
    "conselhos práticos).\n"
    "Regras:\n"
    "- Só ajudas com imóveis, arrendamento, compra e venda em Moçambique. Se a pergunta for "
    "sobre outro assunto (desporto, política, etc.), diz com educação que só ajudas nesses temas.\n"
    "- Para leis, impostos, taxas e documentos usa APENAS a informação de referência. "
    "Não inventes valores, prazos nem instituições. Se a pergunta tiver um valor, faz a conta "
    "com a taxa da referência.\n"
    "- Só indiques instituições que apareçam na referência; se a referência não chegar, "
    "diz que não tens essa informação e sugere um advogado.\n"
    "- A informação é geral e não substitui aconselhamento jurídico.\n"
    "- Nunca recomendes pagar sinal ou caução antes de visitar o imóvel e confirmar o dono.\n"
    "- Para procurar imóveis, indica a pesquisa da Kaya Justa (filtros, preço justo e "
    "alertas de fraude em cada anúncio)."
)


def _temas(pergunta, topico):
    """Até 3 temas com palavras-chave na pergunta (e o tema actual), por relevância."""
    texto = sem_acentos(pergunta)
    contagens = [(sum(1 for p in t.palavras if p in texto), i, t) for i, t in enumerate(assistente.TEMAS)]
    temas = [t for n, _, t in sorted(contagens, key=lambda c: (-c[0], c[1])) if n > 0][:3]
    actual = next((t for t in assistente.TEMAS if t.chave == topico), None)
    if actual and actual not in temas:
        temas.insert(0, actual)
    return temas


def _referencia(pergunta, topico):
    """Texto de referência: os temas reconhecidos pelas regras, ou um resumo de todos."""
    temas = _temas(pergunta, topico)
    if temas:
        return "\n\n".join("\n".join([f"{t.nome}: {t.resposta}", *t.seguimentos.values()]) for t in temas)
    # Sem tema: primeira frase de cada tema (curto, para o modelo responder depressa)
    return "\n".join(f"{t.nome}: {t.resposta.split('. ')[0]}." for t in assistente.TEMAS)


def _mensagens(pergunta, topico, historico):
    msgs = [{"role": "system", "content": INSTRUCOES + "\n\nInformação de referência:\n" + _referencia(pergunta, topico)}]
    for m in historico[-6:]:
        papel = "assistant" if m.get("de") == "assistente" else "user"
        msgs.append({"role": papel, "content": str(m.get("texto", ""))[:1000]})
    msgs.append({"role": "user", "content": pergunta})
    return msgs


def _perguntar_ollama(mensagens):
    corpo = json.dumps({
        "model": settings.OLLAMA_MODELO,
        "messages": mensagens,
        "stream": False,
        "keep_alive": "30m",   # mantém o modelo em memória entre perguntas
        "options": {"temperature": 0.3, "num_predict": 260, "num_ctx": 2048},
    }).encode()
    pedido = urllib.request.Request(f"{settings.OLLAMA_URL}/api/chat", data=corpo,
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=settings.OLLAMA_TEMPO_LIMITE) as resposta:
        texto = json.load(resposta)["message"]["content"].strip()
    if not texto:
        raise ValueError("resposta vazia")
    return texto


def responder(pergunta, topico_anterior=None, historico=()):
    """Mesma interface do assistente por regras, com o campo extra "motor"."""
    base = assistente.responder(pergunta, topico_anterior)
    base["motor"] = "regras"
    if settings.ASSISTENTE_MOTOR != "auto":
        return base
    try:
        base["resposta"] = _perguntar_ollama(_mensagens(pergunta, base["topico"], historico))
        base["motor"] = "ollama"
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError):
        pass   # Ollama desligado, lento ou com erro: fica a resposta das regras
    return base
