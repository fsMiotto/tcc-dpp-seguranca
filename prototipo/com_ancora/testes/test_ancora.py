"""Um teste por cenário da versão com âncora, mais o acréscimo de um registro legítimo."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  #pasta prototipo

from com_ancora import experimento as ex  # noqa: E402
from com_ancora.ancora import MOTIVO_ANCORA, acrescentar_ancorado, verificar_com_ancora  # noqa: E402
from sem_ancora import experimento as sem  # noqa: E402
from sem_ancora.registro import MOTIVO_ENCADEAMENTO, MOTIVO_HASH, MOTIVO_INDICE  # noqa: E402


def confere_falha(nome, posicao, motivo):
    """Detecção na posição e pelo motivo esperados, com a âncora inalterada."""
    _, ancora, _, resultado = ex.aplicar(nome)
    assert not resultado.valida
    assert resultado.posicao_falha == posicao
    assert resultado.motivo == motivo
    assert ancora == ex.cadeia_exemplo()[1]


def test_cadeia_integra():
    _, _, _, resultado = ex.aplicar("Cadeia íntegra")
    assert resultado.valida


def test_alteracao_de_dado():
    confere_falha("Alteração de dado", sem.MEIO, MOTIVO_HASH)


def test_alteracao_do_hash():
    confere_falha("Alteração do hash", sem.MEIO, MOTIVO_HASH)


def test_alteracao_do_registro_do_meio_com_recalculo_do_hash():
    confere_falha("Alteração do registro do meio com recálculo do hash", sem.MEIO + 1, MOTIVO_ENCADEAMENTO)


def test_alteracao_do_ultimo_registro_com_recalculo_do_hash():
    """O hash do último registro não confere com a âncora."""
    confere_falha("Alteração do último registro com recálculo do hash", 4, MOTIVO_ANCORA)


def test_insercao_no_fim_da_cadeia():
    """O novo registro é recusado e a cadeia não cresce."""
    confere_falha(ex.INSERCAO_FIM, 4, MOTIVO_ANCORA)
    cadeia, _, _, _ = ex.aplicar(ex.INSERCAO_FIM)
    assert len(cadeia) == len(sem.EVENTOS)


def test_remocao_no_meio_da_cadeia():
    confere_falha("Remoção no meio da cadeia", sem.MEIO, MOTIVO_INDICE)


def test_remocao_do_ultimo_registro():
    """O novo último registro (3) não é o que a âncora guarda (4)."""
    confere_falha("Remoção do último registro", 3, MOTIVO_ANCORA)


def test_troca_de_ordem():
    confere_falha("Troca de ordem", 1, MOTIVO_INDICE)


def test_reescrita_da_cadeia():
    """A cadeia reescrita é consistente, mas o hash do último registro não é o da âncora."""
    confere_falha("Reescrita da cadeia", 4, MOTIVO_ANCORA)


def test_registro_legitimo_e_aceito():
    cadeia, ancora = ex.cadeia_exemplo()
    assert cadeia == sem.cadeia_exemplo()                                     #mesma cadeia da versão sem âncora
    hash_anterior = ancora.hash
    resultado = acrescentar_ancorado(cadeia, ancora, sem.PRODUTO, *copy.deepcopy(ex.NOVO_EVENTO))
    assert resultado.valida
    assert len(cadeia) == len(sem.EVENTOS) + 1
    assert cadeia[-1]["indice"] == len(sem.EVENTOS)
    assert cadeia[-1]["hash_anterior"] == hash_anterior
    assert (ancora.indice, ancora.hash) == (cadeia[-1]["indice"], cadeia[-1]["hash"])   #âncora atualizada
    assert verificar_com_ancora(cadeia, ancora).valida                        #cadeia válida
