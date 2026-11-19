# Passaporte Digital do Produto e segurança da informação

Código do TCC *Um Estudo Bibliométrico e Protótipo de Segurança da Informação no contexto de Passaporte Digital do Produto* (USP, FFCLRP), que reúne uma análise da literatura sobre o Passaporte Digital do Produto (DPP) e um protótipo de registro encadeado por hash.

## Estrutura

```
analise_literatura/
├── filtragem/      filtros das buscas B1 e B2 (Python)
├── bibliometria/   análise bibliométrica com bibliometrix (R)
└── topicos/        modelagem de tópicos com BERTopic (Python)
prototipo/
├── sem_ancora/     registro encadeado por hash
└── com_ancora/     mesma cadeia com ancoragem externa
```

## Dados da Scopus

As exportações da Scopus e os arquivos derivados com registros completos não são distribuídos. O corpus pode ser obtido na Scopus com as strings de busca do TCC, que estão em `analise_literatura/filtragem/buscas/protocolo_busca.csv`.
