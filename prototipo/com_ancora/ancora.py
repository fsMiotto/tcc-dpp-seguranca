"""Ancoragem externa: índice e hash do último registro guardados fora da cadeia.

O hash e a verificação vêm de sem_ancora/registro.py.
"""
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  #pasta prototipo

from sem_ancora.registro import HASH_INICIAL, Resultado, calcular_hash, verificar  # noqa: E402

MOTIVO_ANCORA = "Último registro diferente da âncora"


@dataclass
class Ancora:
    """Índice e hash do último registro. Cadeia vazia: -1 e HASH_INICIAL."""
    indice: int = -1
    hash: str = HASH_INICIAL


def verificar_com_ancora(cadeia, ancora):
    """Verificação completa e, se passar, comparação do último registro com a âncora."""
    resultado = verificar(cadeia)
    if not resultado.valida:
        return resultado
    indice, hash_ultimo = (cadeia[-1]["indice"], cadeia[-1]["hash"]) if cadeia else (-1, HASH_INICIAL)
    if indice != ancora.indice or hash_ultimo != ancora.hash:
        return Resultado(False, len(cadeia) - 1, MOTIVO_ANCORA)
    return Resultado(True)


def ultimo_confere(cadeia, ancora):
    """Compara índice, hash armazenado e hash recalculado do último registro com a âncora."""
    if not cadeia:
        return ancora.indice == -1 and ancora.hash == HASH_INICIAL
    ultimo = cadeia[-1]
    return ultimo["indice"] == ancora.indice and ultimo["hash"] == ancora.hash and calcular_hash(ultimo) == ancora.hash


def acrescentar_ancorado(cadeia, ancora, produto_id, ator, evento, dados, data_hora):
    """Acrescenta o registro e atualiza a âncora se o último registro conferir; senão, recusa sem alterar nada.
    Não roda a verificação completa (ela é periódica)."""
    if not ultimo_confere(cadeia, ancora):
        return Resultado(False, len(cadeia) - 1, MOTIVO_ANCORA)
    registro = {
        "indice": ancora.indice + 1,
        "produto_id": produto_id,
        "ator": ator,
        "evento": evento,
        "dados": dados,
        "data_hora": data_hora,
        "hash_anterior": ancora.hash,
    }
    registro["hash"] = calcular_hash(registro)
    cadeia.append(registro)
    ancora.indice, ancora.hash = registro["indice"], registro["hash"]
    return Resultado(True)
