"""Modelagem de tópicos (BERTopic) do corpus da B2 filtrada.

Os resultados não guardam os resumos: só EID, título, ano, tópico e palavras.
"""
import os
import re
import sys
import warnings
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from bertopic import BERTopic
from plotly.colors import qualitative
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from termos_seguranca import padroes_seguranca, termo_correspondente, termos_bloco_seguranca

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
warnings.filterwarnings("ignore", message=".*n_jobs value.*overridden.*")  #aviso do UMAP com semente fixa

#Caminhos
PASTA_SCRIPT = Path(__file__).resolve().parent
PASTA_ANALISE = PASTA_SCRIPT.parent
PASTA_BUSCAS = PASTA_ANALISE / "filtragem" / "buscas"
ARQUIVO_PROTOCOLO = PASTA_BUSCAS / "protocolo_busca.csv"
PASTA_CORPUS = PASTA_ANALISE / "filtragem" / "resultados"
PASTA_RESULTADOS = PASTA_SCRIPT / "resultados"

#Corpus
BUSCA = "B2"
TOTAL_DOCS = 242

#Embeddings
MODELO_EMBEDDINGS = "all-MiniLM-L6-v2"
DISPOSITIVO = "cpu"

SEMENTE = 1234

#UMAP
UMAP_VIZINHOS = 15
UMAP_COMPONENTES = 5
UMAP_DIST_MIN = 0.0
UMAP_METRICA = "cosine"

#HDBSCAN (min_cluster_size = min_topic_size)
TAMANHO_MINIMO_TOPICO = 5
HDBSCAN_METRICA = "euclidean"
HDBSCAN_SELECAO = "eom"

#Descrição dos tópicos (c-TF-IDF)
STOP_WORDS = "english"       #lista do scikit-learn
NGRAMAS = (1, 2)
MIN_DF = 2                   #mínimo de documentos com o termo
PALAVRAS_POR_TOPICO = 10
DOCS_REPRESENTATIVOS = 3

#Termo de busca retirado só da descrição dos tópicos (da expressão mais longa para a mais curta)
EXPRESSOES_BUSCA = ["digital product passport", "product passport", "digital passport", "dpp"]

#Gráficos
ESCALA_PNG = 3
CORES_TOPICOS = [qualitative.Dark24[i] for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 14, 22, 18)]
COR_SEM_TOPICO = "#9E9E9E"
MAPA_LARGURA, MAPA_ALTURA = 1200, 675
MAPA_MARGENS = dict(l=180, r=80, t=10, b=10)
MAPA_DOMINIO_X = [0, 0.48]   #fração da largura ocupada pelos pontos; a legenda fica à direita
MAPA_FOLGA_X = 0.04
MAPA_FOLGA_Y = 0.03
MAPA_FONTE_LEGENDA = 24
MAPA_FONTE_NUMERO = 32
MAPA_TAMANHO_PONTO = 7
MARGEM_PADRAO_PLOTLY = 100   #margem de cima padrão do plotly (px)
MARGEM_TOPO_PALAVRAS = 35
MARGEM_TOPO_TEMPO = 20


#---------------------------------------------------------------------------
#Funções
#---------------------------------------------------------------------------
def arquivo_corpus():
    """CSV filtrado da busca, localizado pelo protocolo."""
    protocolo = pd.read_csv(ARQUIVO_PROTOCOLO, dtype=str, encoding="utf-8-sig")
    linha = protocolo[protocolo["Busca"] == BUSCA].iloc[0]
    return PASTA_CORPUS / f"{Path(linha['Arquivo']).stem}_filtrado.csv", linha


def cortar_copyright(resumo):
    """Corta o resumo a partir do primeiro "©"."""
    resumo = "" if pd.isna(resumo) else str(resumo)
    return resumo.split("©", 1)[0].rstrip(), "©" in resumo


PADROES_BUSCA = [re.compile(rf"\b{re.escape(e)}s?\b") for e in EXPRESSOES_BUSCA]


def retirar_termo_busca(texto):
    """Preprocessor do CountVectorizer: minúsculas e sem o termo de busca."""
    texto = texto.lower()
    for padrao in PADROES_BUSCA:
        texto = padrao.sub(" ", texto)
    return texto


def novo_vectorizer(vocabulario):
    return CountVectorizer(preprocessor=retirar_termo_busca, stop_words=STOP_WORDS, ngram_range=NGRAMAS,
                           vocabulary=vocabulario)


def vocabulario_por_documento(textos):
    """Vocabulário com min_df contado por documento (no BERTopic, o vectorizer é ajustado nos tópicos)."""
    limpos = BERTopic(language="english")._preprocess_text(np.array(textos))
    cv = CountVectorizer(preprocessor=retirar_termo_busca, stop_words=STOP_WORDS, ngram_range=NGRAMAS, min_df=MIN_DF)
    cv.fit(limpos)
    return list(cv.get_feature_names_out())


def novo_modelo(vocabulario):
    umap = UMAP(n_neighbors=UMAP_VIZINHOS, n_components=UMAP_COMPONENTES, min_dist=UMAP_DIST_MIN,
                metric=UMAP_METRICA, random_state=SEMENTE)
    hdbscan = HDBSCAN(min_cluster_size=TAMANHO_MINIMO_TOPICO, metric=HDBSCAN_METRICA,
                      cluster_selection_method=HDBSCAN_SELECAO, prediction_data=True)
    #Sem embedding_model, para o BERTopic manter a limpeza do texto antes do c-TF-IDF
    return BERTopic(language="english", umap_model=umap, hdbscan_model=hdbscan,
                    vectorizer_model=novo_vectorizer(vocabulario), top_n_words=PALAVRAS_POR_TOPICO,
                    calculate_probabilities=False)


def rotulo_topico(modelo, t):
    """Número do tópico e as 3 primeiras palavras."""
    return f"{t}: {', '.join(p for p, _ in modelo.get_topic(t)[:3])}"


def separar_numeros(pos, distancia):
    """Afasta os números que ficam mais próximos que a distância (em pixels)."""
    pos = pos.copy()
    for _ in range(500):
        mexeu = False
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                d = pos[j] - pos[i]
                n = np.hypot(*d)
                if n < distancia:
                    direcao = d / n if n > 0 else np.array([1.0, 0.0])
                    passo = (distancia - n) / 2 + 0.5
                    pos[i] -= direcao * passo
                    pos[j] += direcao * passo
                    mexeu = True
        if not mexeu:
            break
    return pos


def salvar_figura(fig, nome):
    fig.write_image(PASTA_RESULTADOS / f"{nome}.png", scale=ESCALA_PNG)


#---------------------------------------------------------------------------
#Entrada
#---------------------------------------------------------------------------
arquivo, linha_busca = arquivo_corpus()
corpus = pd.read_csv(arquivo, encoding="utf-8-sig")
assert len(corpus) == TOTAL_DOCS, f"{arquivo.name} com {len(corpus)} documentos (esperado {TOTAL_DOCS})"
ano_busca = int(str(linha_busca["Data"])[:4])  #gráficos só até o ano da busca

cortes = corpus["Abstract"].map(cortar_copyright)
resumos = [r for r, _ in cortes]
n_cortados = sum(c for _, c in cortes)
textos = [f"{t}. {r}" for t, r in zip(corpus["Title"], resumos)]
titulos = corpus["Title"].tolist()
eids = corpus["EID"].tolist()
anos = corpus["Year"].astype(int).tolist()

print(f"Corpus: {arquivo.name} ({len(corpus)} documentos)")
print(f"Resumos cortados no \"©\": {n_cortados} de {len(corpus)}")

#---------------------------------------------------------------------------
#Modelo
#---------------------------------------------------------------------------
modelo_embeddings = SentenceTransformer(MODELO_EMBEDDINGS, device=DISPOSITIVO)
embeddings = modelo_embeddings.encode(textos, show_progress_bar=False)

vocabulario = vocabulario_por_documento(textos)
modelo = novo_modelo(vocabulario)
topicos, _ = modelo.fit_transform(textos, embeddings)
topicos = list(topicos)

#Todo termo do vocabulário deve aparecer nos documentos juntados por tópico
juntados = pd.DataFrame({"Documento": textos, "Topico": topicos}).groupby("Topico")["Documento"].agg(" ".join)
assert (modelo.vectorizer_model.transform(modelo._preprocess_text(juntados.values)).sum(axis=0) > 0).all(), \
    "Termos do vocabulario sem ocorrencia nos topicos"

PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
lista_topicos = sorted(set(topicos))
contagem = pd.Series(topicos).value_counts()
indice_texto = {t: i for i, t in enumerate(textos)}

#---------------------------------------------------------------------------
#1. topicos.csv
#---------------------------------------------------------------------------
linhas = []
for t in lista_topicos:
    palavras = modelo.get_topic(t)
    representativos = [titulos[indice_texto[d]] for d in (modelo.get_representative_docs(t) or [])][:DOCS_REPRESENTATIVOS]
    representativos += [""] * (DOCS_REPRESENTATIVOS - len(representativos))
    linhas.append([t, int(contagem[t]),
                   "; ".join(p for p, _ in palavras),
                   "; ".join(f"{peso:.4f}" for _, peso in palavras)] + representativos)
colunas = ["Topico", "Documentos", "Palavras", "Pesos_cTFIDF"] + [f"Titulo_representativo_{i}" for i in range(1, DOCS_REPRESENTATIVOS + 1)]
tabela_topicos = pd.DataFrame(linhas, columns=colunas)
tabela_topicos.to_csv(PASTA_RESULTADOS / "topicos.csv", index=False, encoding="utf-8")

#---------------------------------------------------------------------------
#2. documentos_topicos.csv
#---------------------------------------------------------------------------
pd.DataFrame({"EID": eids, "Titulo": titulos, "Ano": anos, "Topico": topicos}).to_csv(
    PASTA_RESULTADOS / "documentos_topicos.csv", index=False, encoding="utf-8")

#---------------------------------------------------------------------------
#3. termos_seguranca_topicos.csv
#---------------------------------------------------------------------------
termos_busca = termos_bloco_seguranca(ARQUIVO_PROTOCOLO, BUSCA)
padroes = padroes_seguranca(termos_busca)

linhas = []
for t in [t for t in lista_topicos if t != -1] + [-1]:
    seg = [(p, termo_correspondente(p, termos_busca, padroes)) for p, _ in modelo.get_topic(t)]
    seg = [(p, ts) for p, ts in seg if ts]
    linhas.append((t, int(contagem[t]),
                   "; ".join(f"{p} [{', '.join(ts)}]" for p, ts in seg)))
tabela_seguranca = pd.DataFrame(linhas, columns=["Topico", "Documentos", "Termos_seguranca [termo da B2]"])
tabela_seguranca.to_csv(PASTA_RESULTADOS / "termos_seguranca_topicos.csv", index=False, encoding="utf-8")

#---------------------------------------------------------------------------
#4. mapa_documentos.png
#---------------------------------------------------------------------------
reduzidos = UMAP(n_neighbors=UMAP_VIZINHOS, n_components=2, min_dist=UMAP_DIST_MIN, metric=UMAP_METRICA,
                 random_state=SEMENTE).fit_transform(embeddings)
np.random.seed(SEMENTE)  #o visualize_documents embaralha os pontos com np.random
fig = modelo.visualize_documents(titulos, reduced_embeddings=reduzidos, hide_annotations=True,
                                 width=MAPA_LARGURA, height=MAPA_ALTURA)
fig.layout.shapes = []
fig.layout.annotations = []
fig.update_layout(title=None)
cores = iter(CORES_TOPICOS)
centros = []                  #(tópico, cor, x, y)
for traco in fig.data:
    traco.marker.size = MAPA_TAMANHO_PONTO
    if traco.name == "other":
        traco.marker.color = COR_SEM_TOPICO
        traco.name = "-1: sem tópico"
        traco.showlegend = True
        traco.legendrank = 2000
    else:
        t = int(traco.name.split("_")[0])
        traco.marker.color = next(cores)
        traco.name = rotulo_topico(modelo, t)
        traco.legendrank = 1000 + t
        traco.mode = "markers"
        dentro = np.array(topicos) == t
        centros.append((t, traco.marker.color, reduzidos[dentro, 0].mean(), reduzidos[dentro, 1].mean()))
x_min, x_max = reduzidos[:, 0].min(), reduzidos[:, 0].max()
y_min, y_max = reduzidos[:, 1].min(), reduzidos[:, 1].max()
rx = [x_min - MAPA_FOLGA_X * (x_max - x_min), x_max + MAPA_FOLGA_X * (x_max - x_min)]
ry = [y_min - MAPA_FOLGA_Y * (y_max - y_min), y_max + MAPA_FOLGA_Y * (y_max - y_min)]
fig.update_xaxes(range=rx, domain=MAPA_DOMINIO_X)
fig.update_yaxes(range=ry, domain=[0, 1])
#Números dos tópicos no centro de cada tópico, afastados quando colidem
larg_area = (MAPA_LARGURA - MAPA_MARGENS["l"] - MAPA_MARGENS["r"]) * (MAPA_DOMINIO_X[1] - MAPA_DOMINIO_X[0])
alt_area = MAPA_ALTURA - MAPA_MARGENS["t"] - MAPA_MARGENS["b"]
pixels = np.array([[(x - rx[0]) / (rx[1] - rx[0]) * larg_area, (y - ry[0]) / (ry[1] - ry[0]) * alt_area]
                   for _, _, x, y in centros])
pixels = separar_numeros(pixels, 1.5 * MAPA_FONTE_NUMERO)
numeros = go.Scattergl(
    x=[rx[0] + p[0] / larg_area * (rx[1] - rx[0]) for p in pixels],
    y=[ry[0] + p[1] / alt_area * (ry[1] - ry[0]) for p in pixels],
    mode="text", text=[str(c[0]) for c in centros],
    textfont=dict(size=MAPA_FONTE_NUMERO, color=[c[1] for c in centros], weight="bold"),
    showlegend=False, hoverinfo="skip")
fig = go.Figure(data=[numeros] + list(fig.data), layout=fig.layout)  #números por baixo dos pontos
fig.update_layout(margin=MAPA_MARGENS, legend=dict(font=dict(size=MAPA_FONTE_LEGENDA), title=None, x=0.5, y=1,
                                                   xanchor="left", yanchor="top", tracegroupgap=0))
salvar_figura(fig, "mapa_documentos")

#---------------------------------------------------------------------------
#5. palavras_topicos.png
#---------------------------------------------------------------------------
n_topicos = len([t for t in lista_topicos if t != -1])
fig = modelo.visualize_barchart(top_n_topics=n_topicos, n_words=PALAVRAS_POR_TOPICO, title="")
for anotacao in fig.layout.annotations:
    anotacao.text = anotacao.text.replace("Topic", "Tópico")
fig.update_layout(margin_t=MARGEM_TOPO_PALAVRAS, height=fig.layout.height - (MARGEM_PADRAO_PLOTLY - MARGEM_TOPO_PALAVRAS))
salvar_figura(fig, "palavras_topicos")

#---------------------------------------------------------------------------
#6. topicos_tempo (CSV com todos os anos; gráfico até o ano da busca)
#---------------------------------------------------------------------------
tempo = modelo.topics_over_time(textos, anos)
tempo.to_csv(PASTA_RESULTADOS / "topicos_tempo.csv", index=False, encoding="utf-8")

anos_grafico = list(range(min(anos), ano_busca + 1))
topicos_grafico = [t for t in lista_topicos if t != -1]
calor = (tempo[tempo["Topic"].isin(topicos_grafico)]
         .pivot_table(index="Topic", columns="Timestamp", values="Frequency", aggfunc="sum")
         .reindex(index=topicos_grafico, columns=anos_grafico, fill_value=0).fillna(0).astype(int))
rotulos = [rotulo_topico(modelo, t) for t in topicos_grafico]
fig = go.Figure(go.Heatmap(z=calor.values, x=[str(a) for a in anos_grafico], y=rotulos, text=calor.values,
                           texttemplate="%{text}", colorscale="Blues", colorbar=dict(title="Documentos")))
fig.update_layout(template="simple_white",
                  width=1000, height=700 - (MARGEM_PADRAO_PLOTLY - MARGEM_TOPO_TEMPO), margin_t=MARGEM_TOPO_TEMPO,
                  xaxis_title="Ano", yaxis_title="Tópico")
fig.update_yaxes(autorange="reversed")
salvar_figura(fig, "topicos_tempo")

#---------------------------------------------------------------------------
#7. parametros.txt
#---------------------------------------------------------------------------
bibliotecas = ["bertopic", "sentence-transformers", "umap-learn", "hdbscan", "scikit-learn", "torch", "numpy",
               "pandas", "plotly", "kaleido"]
texto_parametros = f"""Modelagem de topicos - BERTopic

Python {sys.version.split()[0]}
{chr(10).join(f"{b} {version(b)}" for b in bibliotecas)}

Corpus: {arquivo.name} (busca {BUSCA})
Documentos: {len(corpus)}
Texto: titulo + ". " + resumo, com o resumo cortado no primeiro "©"
Resumos cortados: {n_cortados}

Embeddings: {MODELO_EMBEDDINGS} ({DISPOSITIVO}), texto completo (com o termo de busca), calculados a cada rodada
Semente: {SEMENTE}
UMAP: n_neighbors={UMAP_VIZINHOS}, n_components={UMAP_COMPONENTES}, min_dist={UMAP_DIST_MIN}, metric={UMAP_METRICA}, random_state={SEMENTE}
HDBSCAN: min_cluster_size (min_topic_size)={TAMANHO_MINIMO_TOPICO}, metric={HDBSCAN_METRICA}, cluster_selection_method={HDBSCAN_SELECAO}
Sem reduce_outliers e sem seed_topic_list

Descricao dos topicos: c-TF-IDF padrao, top_n_words={PALAVRAS_POR_TOPICO}
CountVectorizer: stop_words={STOP_WORDS} (scikit-learn), ngram_range={NGRAMAS}
Termo de busca retirado so da descricao (preprocessor, nessa ordem, com plural): {", ".join(EXPRESSOES_BUSCA)}
Vocabulario: {len(vocabulario)} termos
Procedimento do vocabulario: min_df={MIN_DF} aplicado num CountVectorizer separado, ajustado nos {len(corpus)} documentos (um por documento,
  com a mesma limpeza do BERTopic); o vectorizer do BERTopic usa esse vocabulario sem min_df, porque e ajustado nos documentos
  juntados por topico (ali min_df contaria topicos).

Topicos: {n_topicos}
Documentos no topico -1: {topicos.count(-1)}
"""
(PASTA_RESULTADOS / "parametros.txt").write_text(texto_parametros, encoding="utf-8")

#---------------------------------------------------------------------------
#Terminal
#---------------------------------------------------------------------------
print(f"\nTopicos: {n_topicos} | documentos no -1: {topicos.count(-1)} | vocabulario: {len(vocabulario)} termos")
for _, r in tabela_topicos.iterrows():
    print(f"  {r['Topico']:>2} ({r['Documentos']:>3} docs): {r['Palavras']}")
print("\nTermos de seguranca nas palavras dos topicos:")
print(tabela_seguranca.to_string(index=False))
