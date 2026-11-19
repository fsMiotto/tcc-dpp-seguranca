"""Filtra as exportações da Scopus (B1 e B2) e grava os corpora filtrados em resultados/."""
import re
import sys
from pathlib import Path

import pandas as pd

PASTA_SCRIPT = Path(__file__).resolve().parent
PASTA_BUSCAS = PASTA_SCRIPT / "buscas"
PASTA_RESULTADOS = PASTA_SCRIPT / "resultados"
ARQUIVO_PROTOCOLO = PASTA_BUSCAS / "protocolo_busca.csv"
PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)

COLUNAS_PROTOCOLO = {"Busca": "id", "Rotulo": "rotulo", "Data": "data", "Arquivo": "arquivo", "String de busca": "string_busca"}
COLUNA_TITULO = "Title"
COLUNAS_AUXILIARES = ["doi_limpo", "eid_limpo", "titulo_limpo", "chave_titulo", "chave"]
COLUNAS_REVISAR = [COLUNA_TITULO, "Year", "Source title", "DOI", "EID", "Cited by", "arquivo_origem"]

NOMES_CONTAGENS = {
    "id": "Busca",
    "rotulo": "Rotulo",
    "data": "Data",
    "exportados": "Exportados",
    "removidos_ano": "Removidos por Ano",
    "removidos_tipos": "Removidos por Tipo",
    "removidos_id": "Removidos por DOI/EID",
    "removidos_titulo": "Removidos por Titulo",
    "final": "Corpus Final",
}

TIPOS_EXCLUIDOS = [
    "Conference review",
    "Erratum",
    "Editorial",
    "Letter",
    "Note",
    "Short Survey",
    "Retracted",
    "Abstract Report",
]

ANO_MINIMO = 2022  #ano da proposta de regulamento da UE


def limpar(valor):
    """Normaliza o texto para comparação."""
    if pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip().lower()


def salvar(dados, nome):
    """Grava o CSV em resultados/ (sem linhas, apaga o arquivo anterior)."""
    arquivo = PASTA_RESULTADOS / nome
    if len(dados):
        dados.to_csv(arquivo, index=False, encoding="utf-8-sig")
    else:
        arquivo.unlink(missing_ok=True)


def carregar_buscas():
    """Lê as buscas do protocolo_busca.csv."""
    if not ARQUIVO_PROTOCOLO.exists():
        print(f"ERRO: Arquivo de protocolo não encontrado: {ARQUIVO_PROTOCOLO}")
        sys.exit(1)
    buscas = pd.read_csv(ARQUIVO_PROTOCOLO, dtype=str, encoding="utf-8-sig")
    faltando = set(COLUNAS_PROTOCOLO) - set(buscas.columns)
    if faltando:
        print(f"ERRO: Colunas faltando no arquivo de protocolo: {', '.join(faltando)}")
        sys.exit(1)

    return buscas.rename(columns=COLUNAS_PROTOCOLO).to_dict(orient="records")


def remover(dados, mascara, rotulo, busca):
    removidos = dados[mascara].drop(columns=COLUNAS_AUXILIARES, errors="ignore")
    salvar(removidos, f"Removidos_{rotulo}_{busca['id']}.csv")
    return dados[~mascara].copy(), len(removidos)


def preparar_corpus(dados, busca):
    dados = dados.copy()

    for coluna in ["DOI", "EID", COLUNA_TITULO]:
        if coluna not in dados.columns:
            dados[coluna] = ""

    total = len(dados)

    dados, removidos_ano = remover(dados, dados["Year"] < ANO_MINIMO, "ano", busca)
    dados, removidos_tipos = remover(dados, dados["Document Type"].isin(TIPOS_EXCLUIDOS), "tipo", busca)

    dados["doi_limpo"] = dados["DOI"].apply(limpar)
    dados["eid_limpo"] = dados["EID"].apply(limpar)
    dados["titulo_limpo"] = dados[COLUNA_TITULO].apply(limpar)
    dados["chave_titulo"] = dados["titulo_limpo"] + "|" + dados["Year"].astype(str)

    #Chave de duplicata: DOI, depois EID, depois título + ano
    dados["chave"] = dados["doi_limpo"]
    dados.loc[dados["chave"] == "", "chave"] = dados["eid_limpo"]
    dados.loc[dados["chave"] == "", "chave"] = dados["chave_titulo"]

    dados, removidos_id = remover(dados, dados["chave"].duplicated(), "doi_eid", busca)

    #Títulos repetidos, para revisão manual
    repetidos = dados[dados["chave_titulo"].duplicated(keep=False)]
    colunas = [c for c in COLUNAS_REVISAR if c in repetidos.columns]
    salvar(repetidos.sort_values("chave_titulo")[colunas], f"REVISAR_titulos_repetidos_{busca['id']}.csv")

    dados, removidos_titulo = remover(dados, dados["chave_titulo"].duplicated(), "titulo", busca)

    print(f"\n--- {busca['id']} - {busca['rotulo']}")
    print(f"Registros exportados: {total}")
    print(f"Registros removidos por Ano (< {ANO_MINIMO}): {removidos_ano}")
    print(f"Registros removidos por Tipo: {removidos_tipos}")
    print(f"Registros removidos por DOI/EID: {removidos_id}")
    print(f"Registros removidos por título: {removidos_titulo}")
    print(f"Registros finais: {len(dados)}")

    stats = {
        "id": busca["id"],
        "rotulo": busca["rotulo"],
        "data": busca["data"],
        "exportados": total,
        "removidos_tipos": removidos_tipos,
        "removidos_ano": removidos_ano,
        "removidos_titulo": removidos_titulo,
        "removidos_id": removidos_id,
        "final": len(dados)
    }

    return dados.drop(columns=COLUNAS_AUXILIARES), stats


corpora = {}
relatorio = []

for busca in carregar_buscas():
    arquivo = PASTA_BUSCAS / busca["arquivo"]
    if not arquivo.exists():
        print(f"ERRO: Arquivo não encontrado: {arquivo}")
        sys.exit(1)

    df = pd.read_csv(
        arquivo,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    )
    df["busca_id"] = busca["id"]
    df["arquivo_origem"] = busca["arquivo"]

    limpo, stats = preparar_corpus(df, busca)
    relatorio.append(stats)

    salvar(limpo, f"{arquivo.stem}_filtrado.csv")
    corpora[busca["id"]] = limpo


print("\n" + "=" * 40)

if len(corpora) == 2:
    (id_a, a), (id_b, b) = corpora.items()

    fora = b[~b["EID"].isin(set(a["EID"]))]

    print("Aninhamento dos corporas:")
    print(f" - Campo de referência ({id_a}): {len(a)} registros")
    print(f" - Corpus de analise ({id_b}): {len(b)} registros")
    print(f" - Cobertura: {100 * len(b) / len(a):.2f}% do campo trata de seguranca da informacao")

    if len(fora):
        print(f"\n {len(fora)} registros da busca {id_b} não encontrados na busca {id_a}.")
        print(" As duas buscas podem ter sido executadas em momentos diferentes")
        print(fora[[COLUNA_TITULO, "EID"]].to_string(index=False))
    else:
        print(f"\nTodos os registros de {id_b} foram encontrados em {id_a}.")

else:
    print(f"Aviso: {len(corpora)} buscas processadas.")

print("\n" + "=" * 40)
print("CONTAGENS DA FILTRAGEM\n")

tabela = pd.DataFrame(relatorio)[list(NOMES_CONTAGENS)].rename(columns=NOMES_CONTAGENS)
print(tabela.to_string(index=False))
