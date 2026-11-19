# Análise da literatura

- `filtragem/`: filtros das exportações da Scopus (ano, tipo de documento e duplicatas). As strings de busca estão em `buscas/protocolo_busca.csv`.
- `bibliometria/`: análise de desempenho e mapeamento científico com bibliometrix. Os sinônimos das palavras-chave estão em `utils/sinonimos.csv`.
- `topicos/`: modelagem de tópicos com BERTopic.

Os resultados agregados estão nas pastas `resultados/` de cada parte.

## Como rodar

Requer Python 3.12 e R 4.6.1. Coloque as exportações da Scopus (CSV) em `filtragem/buscas/`, com os nomes indicados no `protocolo_busca.csv`, e rode a filtragem antes das outras partes.

Filtragem:

```bash
cd filtragem
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python filtro_corpus.py
```

Bibliometria (as versões dos pacotes estão no `renv.lock`):

```bash
cd bibliometria
Rscript -e 'renv::restore()'
Rscript desempenho.r
Rscript mapeamento.r
```

Tópicos:

```bash
cd topicos
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python topicos.py
```
