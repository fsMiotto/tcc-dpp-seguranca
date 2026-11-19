"""Aplica cada cenário de adulteração a uma cópia da cadeia de exemplo e grava resultados/testes.csv."""
import copy
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  #pasta prototipo

from sem_ancora.registro import acrescentar, calcular_hash, novo_registro, verificar  # noqa: E402

PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"
ARQUIVO_RESULTADOS = PASTA_RESULTADOS / "testes.csv"

PRODUTO = "DPP-BAT-0001"
MEIO = 2                     #registro do meio da cadeia de exemplo

#Eventos do ciclo de vida, com datas fixas
EVENTOS = [
    ("Fabricante A", "fabricação", {"lote": "L-2025-001", "fabrica": "Campinas/SP", "capacidade_kwh": 60},
     "2025-01-15T09:00:00-03:00"),
    ("Transportadora B", "transporte", {"origem": "Campinas/SP", "destino": "Ribeirão Preto/SP"},
     "2025-01-20T14:30:00-03:00"),
    ("Varejista C", "venda", {"loja": "Loja Centro", "nota_fiscal": "NF-000123"},
     "2025-02-03T10:15:00-03:00"),
    ("Assistência D", "reparo", {"peca_trocada": "módulo de células 3", "garantia": True},
     "2026-03-10T16:45:00-03:00"),
    ("Reciclador E", "reciclagem", {"empresa": "Recicla E", "material_recuperado_kg": 42.5},
     "2026-09-28T08:20:00-03:00"),
]


def cadeia_exemplo():
    """Cadeia íntegra com os eventos de EVENTOS."""
    cadeia = []
    for ator, evento, dados, data_hora in EVENTOS:
        acrescentar(cadeia, PRODUTO, ator, evento, dados, data_hora)
    return cadeia


#---------------------------------------------------------------------------
#Cenários: recebem uma cópia da cadeia e devolvem (cadeia alterada, registro afetado)
#---------------------------------------------------------------------------
def cenario_integra(cadeia):
    return cadeia, "nenhum"


def cenario_alteracao_dado(cadeia):
    cadeia[MEIO]["dados"]["loja"] = "Loja Falsa"
    return cadeia, f"{MEIO}"


def cenario_alteracao_hash(cadeia):
    cadeia[MEIO]["hash"] = "f" * 64
    return cadeia, f"{MEIO}"


def cenario_recalculo_meio(cadeia):
    """Altera o registro do meio e recalcula só o hash dele."""
    cadeia[MEIO]["dados"]["loja"] = "Loja Falsa"
    cadeia[MEIO]["hash"] = calcular_hash(cadeia[MEIO])
    return cadeia, f"{MEIO}"


def cenario_recalculo_ultimo(cadeia):
    """Altera o último registro e recalcula o hash dele."""
    ultimo = len(cadeia) - 1
    cadeia[ultimo]["dados"]["material_recuperado_kg"] = 10.0
    cadeia[ultimo]["hash"] = calcular_hash(cadeia[ultimo])
    return cadeia, f"{ultimo} (último)"


def cenario_insercao(cadeia):
    """Insere no meio um registro novo bem formado em relação ao anterior."""
    falso = novo_registro(cadeia[:MEIO], PRODUTO, "Varejista X", "venda", {"loja": "Loja Paralela"},
                          "2025-01-25T11:00:00-03:00")
    cadeia.insert(MEIO, falso)
    return cadeia, f"novo registro na posição {MEIO}"


def cenario_remocao(cadeia):
    del cadeia[MEIO]
    return cadeia, f"{MEIO} (removido)"


def cenario_remocao_ultimo(cadeia):
    """Remove o último registro, sem outra alteração."""
    ultimo = len(cadeia) - 1
    del cadeia[ultimo]
    return cadeia, f"{ultimo} (removido)"


def cenario_troca_ordem(cadeia):
    cadeia[1], cadeia[3] = cadeia[3], cadeia[1]
    return cadeia, "1 e 3"


def cenario_reescrita(cadeia):
    """Altera o registro do meio e recalcula o hash dele e de todos os seguintes."""
    cadeia[MEIO]["dados"]["loja"] = "Loja Falsa"
    for posicao in range(MEIO, len(cadeia)):
        cadeia[posicao]["hash_anterior"] = cadeia[posicao - 1]["hash"]
        cadeia[posicao]["hash"] = calcular_hash(cadeia[posicao])
    return cadeia, f"{MEIO} (e hashes de {MEIO} a {len(cadeia) - 1} recalculados)"


CENARIOS = [
    ("Cadeia íntegra", cenario_integra),
    ("Alteração de dado", cenario_alteracao_dado),
    ("Alteração do hash", cenario_alteracao_hash),
    ("Alteração do registro do meio com recálculo do hash", cenario_recalculo_meio),
    ("Alteração do último registro com recálculo do hash", cenario_recalculo_ultimo),
    ("Inserção no meio da cadeia", cenario_insercao),
    ("Remoção no meio da cadeia", cenario_remocao),
    ("Remoção do último registro", cenario_remocao_ultimo),
    ("Troca de ordem", cenario_troca_ordem),
    ("Reescrita da cadeia", cenario_reescrita),
]


def aplicar(cenario):
    """Aplica o cenário a uma cópia da cadeia e verifica. Devolve (cadeia, afetado, resultado)."""
    cadeia, afetado = cenario(copy.deepcopy(cadeia_exemplo()))
    return cadeia, afetado, verificar(cadeia)


def main():
    linhas = []
    for nome, cenario in CENARIOS:
        _, afetado, resultado = aplicar(cenario)
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
