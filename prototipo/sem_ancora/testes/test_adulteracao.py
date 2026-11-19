"""Um teste por cenário da versão sem âncora."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  #pasta prototipo

from sem_ancora import experimento as ex  # noqa: E402
from sem_ancora.registro import MOTIVO_ENCADEAMENTO, MOTIVO_HASH, MOTIVO_INDICE, verificar  # noqa: E402


def test_cadeia_integra():
    _, _, resultado = ex.aplicar(ex.cenario_integra)
    assert resultado.valida


def test_alteracao_de_dado():
    _, _, resultado = ex.aplicar(ex.cenario_alteracao_dado)
    assert not resultado.valida
    assert resultado.posicao_falha == ex.MEIO
    assert resultado.motivo == MOTIVO_HASH


def test_alteracao_do_hash():
    _, _, resultado = ex.aplicar(ex.cenario_alteracao_hash)
    assert not resultado.valida
    assert resultado.posicao_falha == ex.MEIO
    assert resultado.motivo == MOTIVO_HASH


def test_alteracao_com_recalculo_do_hash_meio():
    """O registro seguinte ainda guarda o hash antigo como hash_anterior."""
    _, _, resultado = ex.aplicar(ex.cenario_recalculo_meio)
    assert not resultado.valida
    assert resultado.posicao_falha == ex.MEIO + 1
    assert resultado.motivo == MOTIVO_ENCADEAMENTO


def test_alteracao_com_recalculo_do_hash_ultimo_nao_e_detectada():
    """Nada aponta para o hash do último registro: a alteração não é detectada."""
    original = ex.cadeia_exemplo()
    alterada, _, resultado = ex.aplicar(ex.cenario_recalculo_ultimo)
    assert resultado.valida                                                   #não detectado
    assert alterada[-1]["dados"] != original[-1]["dados"]                     #o dado foi mesmo alterado
    assert alterada[-1]["hash"] != original[-1]["hash"]                       #e o hash também
    assert alterada[:-1] == original[:-1]                                     #os outros registros não mudaram


def test_insercao():
    """A falha aparece no registro seguinte ao inserido."""
    _, _, resultado = ex.aplicar(ex.cenario_insercao)
    assert not resultado.valida
    assert resultado.posicao_falha == ex.MEIO + 1
    assert resultado.motivo == MOTIVO_INDICE


def test_remocao():
    _, _, resultado = ex.aplicar(ex.cenario_remocao)
    assert not resultado.valida
    assert resultado.posicao_falha == ex.MEIO
    assert resultado.motivo == MOTIVO_INDICE


def test_remocao_do_ultimo_registro_nao_e_detectada():
    """A cadeia mais curta continua válida: a remoção não é detectada."""
    original = ex.cadeia_exemplo()
    alterada, _, resultado = ex.aplicar(ex.cenario_remocao_ultimo)
    assert resultado.valida                                                   #não detectado
    assert len(alterada) == len(original) - 1                                 #o registro foi mesmo removido
    assert alterada == original[:-1]                                          #os outros registros não mudaram


def test_troca_de_ordem():
    _, _, resultado = ex.aplicar(ex.cenario_troca_ordem)
    assert not resultado.valida
    assert resultado.posicao_falha == 1
    assert resultado.motivo == MOTIVO_INDICE


def test_reescrita_da_cadeia_nao_e_detectada():
    """Limite do mecanismo: a cadeia reescrita é consistente e a alteração não é detectada."""
    original = ex.cadeia_exemplo()
    reescrita, _, resultado = ex.aplicar(ex.cenario_reescrita)
    assert verificar(original).valida
    assert resultado.valida                                                   #não detectado
    assert reescrita[ex.MEIO]["dados"] != original[ex.MEIO]["dados"]          #o dado foi mesmo alterado
    assert all(reescrita[i]["hash"] != original[i]["hash"] for i in range(ex.MEIO, len(original)))
    assert reescrita[-1]["hash"] != original[-1]["hash"]
