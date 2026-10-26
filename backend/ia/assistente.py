"""
Assistente Virtual baseado em regras (RF09, UC09).

Funcionamento:
  1. A pergunta é normalizada (minúsculas, sem acentos).
  2. Procura-se o tema cujas palavras-chave aparecem mais vezes.
  3. Se nenhum tema for reconhecido mas o cliente indicar o tema da pergunta
     anterior, trata-se como pergunta complementar desse tema (TC10).
  4. Dentro do tema, uma palavra de seguimento ("prazo", "custo", ...) pode
     escolher uma resposta mais específica.

As respostas são informação geral e não substituem aconselhamento jurídico.
"""
from dataclasses import dataclass

from .risco import sem_acentos


@dataclass
class Tema:
    chave: str
    nome: str
    palavras: list
    resposta: str
    seguimentos: dict   # palavra -> resposta específica


TEMAS = [
    Tema("duat", "DUAT", ["duat", "direito de uso", "terra", "terreno", "talhao"],
         "O DUAT (Direito de Uso e Aproveitamento da Terra) é o título que permite usar "
         "um terreno. Em Moçambique a terra é propriedade do Estado e não se vende; o que "
         "se transmite são o DUAT e as construções. Antes de pagar por um terreno, peça a "
         "cópia do DUAT e confirme-o nos Serviços de Cadastro ou no Conselho Municipal.",
         {"onde": "Em zonas urbanas o pedido e a verificação fazem-se no Conselho Municipal "
                  "(área de cadastro). Fora delas, nos Serviços Provinciais de Geografia e Cadastro.",
          "document": "Normalmente pedem: documento de identificação, NUIT, planta de localização "
                      "do terreno e, quando aplicável, o parecer da comunidade local.",
          "prazo": "O prazo varia com o município e o tipo de pedido. Peça sempre um "
                   "comprovativo de entrada do processo."}),
    Tema("caucao", "Caução", ["caucao", "garantia", "deposito", "adiantamento"],
         "A caução é um valor entregue ao senhorio no início do arrendamento para cobrir "
         "danos ou rendas em falta. É habitual corresponder a 1 a 3 meses de renda, mas é "
         "negociável. Exija recibo e que o valor e as condições de devolução fiquem no contrato.",
         {"devol": "A caução deve ser devolvida no fim do contrato, descontando apenas danos "
                   "comprovados ou dívidas. Faça uma vistoria com fotografias na entrada e na saída.",
          "quanto": "O mais comum é 1 a 3 meses de renda. Desconfie de pedidos muito superiores "
                    "ou de caução exigida antes de visitar o imóvel."}),
    Tema("sisa", "SISA", ["sisa", "imposto", "transmissao", "compra e venda"],
         "A SISA é o imposto pago pelo comprador na transmissão onerosa de um imóvel. A taxa "
         "geral é de 2% sobre o valor da transmissão (ou o valor patrimonial, se for maior). "
         "Deve ser paga antes da escritura. Confirme o valor junto da Autoridade Tributária.",
         {"quem": "Quem paga a SISA é o comprador.",
          "quando": "A SISA é liquidada antes da escritura pública de compra e venda; o "
                    "notário pede o comprovativo.",
          "calcul": "Exemplo: numa compra de 5 000 000 MT, a SISA a 2% seria 100 000 MT."}),
    Tema("ipra", "IPRA", ["ipra", "imposto predial", "autarquico"],
         "O IPRA (Imposto Predial Autárquico) é pago anualmente ao município pelo "
         "proprietário do imóvel, calculado sobre o valor patrimonial. As taxas são "
         "definidas por cada município; confirme no Conselho Municipal da sua cidade.", {}),
    Tema("contrato", "Contrato de arrendamento", ["contrato", "arrendamento", "renda", "senhorio"],
         "O contrato de arrendamento deve ser escrito e indicar: identificação das partes, "
         "imóvel, valor e data de pagamento da renda, duração, caução, quem paga água e "
         "energia, e as condições de saída. Leia tudo antes de assinar e guarde uma cópia.",
         {"prazo": "A duração é acordada entre as partes. Verifique o pré-aviso exigido para "
                   "sair antes do fim e as regras de renovação.",
          "aument": "Aumentos de renda devem seguir o que está no contrato. Peça que a regra "
                    "de actualização fique escrita."}),
    Tema("compra", "Documentos para comprar", ["comprar", "compra", "escritura", "conservatoria",
                                                "registo predial", "documentos"],
         "Para comprar com segurança: peça a certidão do registo predial (confirma quem é o "
         "dono e se há hipotecas), o DUAT ou título do terreno, a planta aprovada e o "
         "comprovativo de IPRA pago. A escritura faz-se no notário e depois regista-se na "
         "Conservatória do Registo Predial.",
         {"certid": "A certidão do registo predial pede-se na Conservatória do Registo Predial "
                    "da área do imóvel."}),
    Tema("fraude", "Segurança e fraude", ["fraude", "burla", "seguro", "confiar", "golpe", "alerta"],
         "Sinais de alerta: preço muito abaixo do mercado, pedido de pagamento antes da "
         "visita, anunciante que diz estar fora do país, fotografias repetidas noutros "
         "anúncios. Nunca pague sem visitar o imóvel e confirmar o dono. Os anúncios com "
         "risco detectado mostram um indicador vermelho.", {}),
    Tema("preco", "Preço justo", ["preco justo", "estimativa", "caro", "barato", "vale"],
         "O preço justo é uma estimativa calculada a partir de anúncios semelhantes "
         "publicados na plataforma (zona, tipo, área e número de divisões). Mostramos também "
         "um intervalo: preços dentro dele são considerados normais para a zona.", {}),
    Tema("publicar", "Publicar anúncio", ["publicar", "anunciar", "vender o meu", "arrendar o meu"],
         "Para publicar, crie uma conta de Proprietário/Agência, abra «Novo anúncio», "
         "preencha os dados e as fotografias e submeta. O anúncio passa pela análise "
         "automática e pela moderação antes de ficar visível.", {}),
]

RESPOSTA_DESCONHECIDA = (
    "Não percebi a pergunta. Posso ajudar com: DUAT, caução, SISA, IPRA, contrato de "
    "arrendamento, documentos para comprar, segurança e fraude, preço justo e publicação "
    "de anúncios.")


def responder(pergunta, topico_anterior=None):
    """Devolve um dicionário com a resposta, o tema e sugestões de seguimento."""
    texto = sem_acentos(pergunta)

    # Passo 2: tema com mais palavras-chave encontradas
    melhor, contagem = None, 0
    for tema in TEMAS:
        n = sum(1 for p in tema.palavras if p in texto)
        if n > contagem:
            melhor, contagem = tema, n

    # Passo 3: pergunta complementar do tema anterior
    complementar = False
    if melhor is None and topico_anterior:
        melhor = next((t for t in TEMAS if t.chave == topico_anterior), None)
        complementar = melhor is not None

    if melhor is None:
        return {"resposta": RESPOSTA_DESCONHECIDA, "topico": None, "sugestoes": [
            "O que é o DUAT?", "Quanto é a caução?", "Quanto se paga de SISA?"]}

    # Passo 4: resposta específica dentro do tema
    resposta = melhor.resposta
    for palavra, especifica in melhor.seguimentos.items():
        if palavra in texto:
            resposta = especifica
            break
    else:
        if complementar:
            resposta = f"Sobre {melhor.nome}: {melhor.resposta}"

    return {"resposta": resposta, "topico": melhor.chave,
            "sugestoes": _sugestoes(melhor)}


def _sugestoes(tema):
    exemplos = {
        "duat": ["Onde se trata o DUAT?", "Que documentos são precisos?"],
        "caucao": ["Quanto costuma ser?", "Quando é devolvida?"],
        "sisa": ["Quem paga?", "Como se calcula?"],
        "contrato": ["Qual o prazo?", "Como funcionam os aumentos?"],
        "compra": ["Onde peço a certidão?"],
    }
    return exemplos.get(tema.chave, ["O que é o DUAT?", "Como evitar burlas?"])
