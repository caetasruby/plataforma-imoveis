"""
Módulo Verificação de Imagens (CT02, RNF02).

Cada fotografia recebe uma "impressão digital" (hash SHA-256) calculada a
partir dos seus bytes. Duas fotografias iguais têm o mesmo hash, por isso
basta procurar o hash na base de dados para saber se a imagem já foi usada
noutro anúncio.
"""
import hashlib


def calcular_hash(ficheiro):
    """Lê o ficheiro em blocos (não carrega tudo na memória) e devolve o hash."""
    sha = hashlib.sha256()
    ficheiro.seek(0)
    for bloco in iter(lambda: ficheiro.read(64 * 1024), b""):
        sha.update(bloco)
    ficheiro.seek(0)
    return sha.hexdigest()


def contar_duplicadas(anuncio):
    """Marca e conta as fotografias do anúncio que já existem noutro anúncio."""
    from anuncios.models import ImagemImovel

    duplicadas = 0
    for imagem in anuncio.imagens.all():
        existe = (ImagemImovel.objects.filter(checksum_hash=imagem.checksum_hash)
                  .exclude(anuncio=anuncio).exists())
        if existe != imagem.eh_duplicada:
            imagem.eh_duplicada = existe
            imagem.save(update_fields=["eh_duplicada"])
        duplicadas += int(existe)
    return duplicadas
