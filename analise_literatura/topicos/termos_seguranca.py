"""Termos de segurança: palavras que correspondem a um termo do bloco de segurança da string da B2.

O * é truncagem; maiúsculas e hifens são ignorados.
"""
import re

import pandas as pd


def sem_hifen(texto):
    return str(texto).lower().replace("-", "")


def termos_bloco_seguranca(arquivo_protocolo, busca="B2"):
    """Termos do bloco de segurança (o que vem depois do AND na string da busca)."""
    protocolo = pd.read_csv(arquivo_protocolo, encoding="utf-8-sig")
    string_busca = protocolo.loc[protocolo["Busca"] == busca, "String de busca"].iloc[0]
    bloco = string_busca.split(" AND ", 1)[1]
    termos = [entre_aspas or solto for entre_aspas, solto in re.findall(r'"([^"]+)"|([^\s()"]+)', bloco)]
    return [t for t in termos if t != "OR"]


def padroes_seguranca(termos):
    """Um padrão por termo, a partir do início da palavra: com * aceita qualquer continuação; sem *, só o plural em "s"."""
    return [re.compile(r"\b" + re.escape(sem_hifen(t.rstrip("*"))) + (r"\w*" if t.endswith("*") else r"s?\b"))
            for t in termos]


def e_seguranca(palavra, padroes):
    return any(p.search(sem_hifen(palavra)) for p in padroes)


def termo_correspondente(palavra, termos, padroes):
    """Termos da busca que correspondem à palavra (vazio se nenhum)."""
    return [t for t, p in zip(termos, padroes) if p.search(sem_hifen(palavra))]
