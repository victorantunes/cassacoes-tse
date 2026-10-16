"""Baixa os arquivos de candidatos do Portal de Dados Abertos do TSE para uma pasta de cache.

Uso: python scripts/01_baixar_tse.py [pasta_cache]
"""
import pathlib
import sys
import urllib.request

ANOS = list(range(1994, 2025, 2))
BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele"


def main(cache="cache"):
    pasta = pathlib.Path(cache)
    pasta.mkdir(exist_ok=True)
    alvos = [(f"consulta_cand_{a}.zip", f"{BASE}/consulta_cand/consulta_cand_{a}.zip") for a in ANOS]
    alvos.append(("motivo_cassacao_2024.zip", f"{BASE}/motivo_cassacao/motivo_cassacao_2024.zip"))
    for nome, url in alvos:
        destino = pasta / nome
        if not destino.exists():
            print("baixando", nome)
            urllib.request.urlretrieve(url, destino)


if __name__ == "__main__":
    main(*sys.argv[1:])
