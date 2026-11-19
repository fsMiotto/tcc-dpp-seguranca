# Protótipo

Registro encadeado por hash para o Passaporte Digital do Produto, com testes de cenários de adulteração.

- `sem_ancora/`: cadeia de registros, cálculo do hash (SHA-256) e verificação.
- `com_ancora/`: a mesma cadeia com ancoragem externa (índice e hash do último registro guardados fora da cadeia).

Cada versão tem os testes em `testes/` e os resultados do experimento em `resultados/testes.csv`.

## Como rodar

Requer Python 3.12. Rode os comandos dentro da pasta `prototipo/`:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pytest sem_ancora com_ancora -v
.venv/bin/python sem_ancora/experimento.py
.venv/bin/python com_ancora/experimento.py
```
