"""Registro encadeado por hash para o Passaporte Digital do Produto (DPP).

Registro: dicionário com indice, produto_id, ator, evento, dados, data_hora, hash_anterior e hash.
"""
import hashlib
import json
from dataclasses import dataclass

HASH_INICIAL = "0" * 64      #hash_anterior do primeiro registro

MOTIVO_INDICE = "índice fora da sequência"
MOTIVO_HASH = "hash armazenado diferente do recalculado"
MOTIVO_ENCADEAMENTO = "hash_anterior diferente do hash do registro anterior"


def serializar(conteudo):
    """JSON canônico: chaves ordenadas, sem espaços, em UTF-8."""
    return json.dumps(conteudo, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def calcular_hash(registro):
    """SHA-256 de todos os campos, menos o próprio hash."""
    conteudo = {campo: valor for campo, valor in registro.items() if campo != "hash"}
    return hashlib.sha256(serializar(conteudo)).hexdigest()


def novo_registro(cadeia, produto_id, ator, evento, dados, data_hora):
    """Registro seguinte da cadeia, com o hash calculado."""
    registro = {
        "indice": len(cadeia),
        "produto_id": produto_id,
        "ator": ator,
        "evento": evento,
        "dados": dados,
        "data_hora": data_hora,
        "hash_anterior": cadeia[-1]["hash"] if cadeia else HASH_INICIAL,
    }
    registro["hash"] = calcular_hash(registro)
    return registro


def acrescentar(cadeia, produto_id, ator, evento, dados, data_hora):
    """Acrescenta um registro ao fim da cadeia e o devolve."""
    registro = novo_registro(cadeia, produto_id, ator, evento, dados, data_hora)
    cadeia.append(registro)
    return registro


@dataclass
class Resultado:
    valida: bool
    posicao_falha: int | None = None
    motivo: str | None = None


def verificar(cadeia):
    """Confere índice, hash e encadeamento de cada registro e para na primeira falha."""
    for posicao, registro in enumerate(cadeia):
        if registro["indice"] != posicao:
            return Resultado(False, posicao, MOTIVO_INDICE)
        if registro["hash"] != calcular_hash(registro):
            return Resultado(False, posicao, MOTIVO_HASH)
        esperado = cadeia[posicao - 1]["hash"] if posicao > 0 else HASH_INICIAL
        if registro["hash_anterior"] != esperado:
            return Resultado(False, posicao, MOTIVO_ENCADEAMENTO)
    return Resultado(True)
