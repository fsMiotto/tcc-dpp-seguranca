"""Aplica os cenários à cadeia com âncora e grava resultados/testes.csv. O atacante não altera a âncora."""
import copy
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  #pasta prototipo

from com_ancora.ancora import Ancora, acrescentar_ancorado, verificar_com_ancora  # noqa: E402
from sem_ancora import experimento as sem  # noqa: E402

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"
ARQUIVO_RESULTADOS = PASTA_RESULTADOS / "testes.csv"

INSERCAO_FIM = "Inserção no fim da cadeia"
NOVO_EVENTO = ("Auditor F", "auditoria", {"resultado": "conforme"}, "2026-10-05T10:00:00-03:00")   #registro legítimo


def cadeia_exemplo():
    """Mesma cadeia da versão sem âncora, montada com acrescentar_ancorado. Devolve (cadeia, ancora)."""
    cadeia, ancora = [], Ancora()
    for ator, evento, dados, data_hora in sem.EVENTOS:
        resultado = acrescentar_ancorado(cadeia, ancora, sem.PRODUTO, ator, evento, copy.deepcopy(dados), data_hora)
        assert resultado.valida
    return cadeia, ancora


def cenario_insercao_fim(cadeia, ancora):
    """Altera o último registro, recalcula o hash dele e tenta acrescentar um registro legítimo."""
    cadeia, afetado = sem.cenario_recalculo_ultimo(cadeia)
    return cadeia, afetado, acrescentar_ancorado(cadeia, ancora, sem.PRODUTO, *NOVO_EVENTO)


def com_verificacao(cenario):
    """Cenário da versão sem âncora seguido da verificação com âncora."""
    def aplicar_cenario(cadeia, ancora):
        cadeia, afetado = cenario(cadeia)
        return cadeia, afetado, verificar_com_ancora(cadeia, ancora)
    return aplicar_cenario


#Cenários da versão sem âncora, com a inserção no fim no lugar da inserção no meio
CENARIOS = [(INSERCAO_FIM, cenario_insercao_fim) if cenario is sem.cenario_insercao else (nome, com_verificacao(cenario))
            for nome, cenario in sem.CENARIOS]


def aplicar(nome):
    """Aplica o cenário a uma cópia da cadeia. Devolve (cadeia, ancora, afetado, resultado)."""
    cadeia, ancora = cadeia_exemplo()
    cadeia, afetado, resultado = dict(CENARIOS)[nome](copy.deepcopy(cadeia), ancora)
    return cadeia, ancora, afetado, resultado


def main():
    linhas = []
    for nome, _ in CENARIOS:
        _, _, afetado, resultado = aplicar(nome)
        detectado = not resultado.valida
        linhas.append([nome, afetado, "sim" if detectado else "não",
                       resultado.posicao_falha if detectado else "", resultado.motivo or ""])

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_RESULTADOS, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["Cenário", "Registro afetado", "Detectado", "Registro em que a verificação falhou", "Motivo"])
        escritor.writerows(linhas)

    for linha in linhas:
        print(" | ".join(str(c) for c in linha))
    print(f"\nResultados em {ARQUIVO_RESULTADOS}")


if __name__ == "__main__":
    main()
