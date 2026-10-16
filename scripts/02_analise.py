"""Contagem de eleitos cassados por partido e espectro, normalizada por mandatos eleitos.

Uso: python scripts/02_analise.py [pasta_cache] [pasta_saida]
"""
import collections
import csv
import datetime
import io
import json
import math
import pathlib
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from partidos import BLOCO, CATEGORIAS, canon, categoria, escala_2023, escala_2025  # noqa: E402

csv.field_size_limit(10**9)
RAIZ = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "cache")
SAIDA = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else RAIZ / "data")
SAIDA.mkdir(exist_ok=True)

MUN = [2000, 2004, 2008, 2012, 2016, 2020, 2024]        # eleições municipais
GER = [1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022]  # eleições gerais
CICLOS_PREFEITO = [2004, 2008, 2012, 2016, 2020, 2024]  # ciclos com dados de eleições suplementares
NIVEIS = ["prefeito", "deputado", "senador", "governador"]


def linhas(ano):
    with zipfile.ZipFile(CACHE / f"consulta_cand_{ano}.zip") as z:
        with z.open(f"consulta_cand_{ano}_BRASIL.csv") as f:
            yield from csv.DictReader(io.TextIOWrapper(f, encoding="latin-1", newline=""), delimiter=";")


def eleito(r):
    s = (r.get("DS_SIT_TOT_TURNO") or "").upper()
    return s.startswith("ELEITO") or s == "MÉDIA"


def ordinaria(r):
    return ("SUPLEMENTAR" not in (r.get("NM_TIPO_ELEICAO") or "").upper()
            and "SUPLEMENTAR" not in (r.get("DS_ELEICAO") or "").upper())


def marcador_tse(r):
    for k in ("DS_SITUACAO_CANDIDATURA", "DS_DETALHE_SITUACAO_CAND", "DS_SIT_TOT_TURNO"):
        v = (r.get(k) or "").upper()
        if v in ("CASSADO", "CASSADO COM RECURSO") or (v.startswith("CASSA") and "REGISTRO" in v):
            return f"{k}={r.get(k)}"
    return None


# ------------------------------------------------------------------ leitura dos arquivos do TSE
den = collections.Counter()     # (nível, partido) -> mandatos eleitos
prefeito_eleito = {}            # (ciclo, SG_UE) -> (partido canônico, nome, sigla original)
sup_prefeito = {}               # (ciclo, SG_UE) -> data da primeira eleição suplementar
tse_marcados = []               # eleitos municipais com registro/diploma cassado (marcador do TSE)
sq_cassacao_2024 = set()

with zipfile.ZipFile(CACHE / "motivo_cassacao_2024.zip") as z:
    with z.open("motivo_cassacao_2024_BRASIL.csv") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1", newline=""), delimiter=";"):
            if "cassa" in r["DS_TP_MOTIVO"].lower() and "julgamento" not in r["DS_TP_MOTIVO"].lower():
                sq_cassacao_2024.add(r["SQ_CANDIDATO"])

for ano in sorted(set(MUN) | set(GER)):
    for r in linhas(ano):
        cargo = (r.get("DS_CARGO") or "").upper()
        p = canon(r["SG_PARTIDO"], ano)
        if ano in GER and ordinaria(r) and eleito(r):
            if cargo == "DEPUTADO FEDERAL":
                den[("deputado", p)] += 1
            elif cargo == "GOVERNADOR":
                den[("governador", p)] += 1
            elif cargo == "SENADOR":
                den[("senador", p)] += 1
        if ano not in MUN:
            continue
        if ordinaria(r) and eleito(r) and cargo == "PREFEITO":
            prefeito_eleito[(ano, r["SG_UE"])] = (p, r["NM_CANDIDATO"], r["SG_PARTIDO"])
            if ano in CICLOS_PREFEITO:
                den[("prefeito", p)] += 1
        if not ordinaria(r) and cargo == "PREFEITO":
            d = datetime.datetime.strptime(r["DT_ELEICAO"], "%d/%m/%Y")
            ciclo = (d.year - 1) - ((d.year - 1 - 2000) % 4)   # mandato vai de 1º/jan do ano seguinte à eleição ao fim de 4 anos
            chave = (ciclo, r["SG_UE"])
            if chave not in sup_prefeito or d.date() < sup_prefeito[chave]:
                sup_prefeito[chave] = d.date()
        marca = marcador_tse(r)
        if not marca and ano == 2024 and r.get("SQ_CANDIDATO") in sq_cassacao_2024:
            marca = "motivo_cassacao_2024: fundamento de cassação"
        if marca and ordinaria(r) and eleito(r) and cargo in ("PREFEITO", "VICE-PREFEITO", "VEREADOR"):
            tse_marcados.append(dict(
                ano=ano, cargo=cargo.title(), uf=r["SG_UF"], municipio=r["NM_UE"].title(),
                nome=r["NM_CANDIDATO"].title(), partido_na_eleicao=r["SG_PARTIDO"],
                resultado=r["DS_SIT_TOT_TURNO"], marcador=marca))

# ------------------------------------------------------------------ casos
casos = []
suplementares = []
vistos = set()
sem_prefeito = 0
sem_ciclo = collections.Counter()
for (ciclo, ue), data in sorted(sup_prefeito.items()):
    if ciclo not in CICLOS_PREFEITO:
        continue
    if (ciclo, ue) not in prefeito_eleito:
        sem_prefeito += 1
        sem_ciclo[ciclo] += 1
        continue
    p, nome, sigla = prefeito_eleito[(ciclo, ue)]
    vistos.add((ciclo, ue))
    suplementares.append(dict(ciclo=ciclo, codigo_municipio=ue, prefeito_eleito=nome.title(),
                              partido_na_eleicao=sigla, data_suplementar=data.isoformat()))
    casos.append(dict(nivel="prefeito", ano=ciclo, partido=p, nome=nome.title(), origem="eleição suplementar"))

por_nome = {(c, v[1].title()): ue for (c, ue), v in prefeito_eleito.items()}
extra_marcados = 0
for m in tse_marcados:
    if m["cargo"] == "Prefeito" and m["ano"] in CICLOS_PREFEITO:
        ue = por_nome.get((m["ano"], m["nome"]))
        if ue is None or (m["ano"], ue) not in vistos:
            extra_marcados += 1
            casos.append(dict(nivel="prefeito", ano=m["ano"], partido=canon(m["partido_na_eleicao"], m["ano"]),
                              nome=m["nome"], origem="marcador do TSE"))

altos = list(csv.DictReader(open(RAIZ / "data" / "altos_cargos_cassados.csv", encoding="utf-8"), delimiter=";"))
NIVEL_DE = {"Deputado federal": "deputado", "Senador": "senador", "Governador": "governador", "Presidente": "presidente"}
for a in altos:
    nv = NIVEL_DE[a["cargo"]]
    a["partido_canonico"] = canon(a["partido_na_eleicao"], int(a["ano"]))
    a["categoria_2023"] = categoria(escala_2023(a["partido_canonico"]))
    fora = nv == "presidente" or (nv == "deputado" and int(a["ano"]) < 1998)
    a["no_universo_normalizado"] = "não" if fora else "sim"
    if not fora:
        casos.append(dict(nivel=nv, ano=int(a["ano"]), partido=a["partido_canonico"], nome=a["nome"], origem="lista manual"))


# ------------------------------------------------------------------ estatística
def fisher(a, b, c, d):
    """Teste exato de Fisher bilateral para a tabela [[a, b], [c, d]]."""
    n1, n2, k = a + b, c + d, a + c
    n = n1 + n2

    def lp(x):
        return (math.lgamma(n1 + 1) - math.lgamma(x + 1) - math.lgamma(n1 - x + 1)
                + math.lgamma(n2 + 1) - math.lgamma(k - x + 1) - math.lgamma(n2 - k + x + 1)
                - (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)))

    obs = lp(a)
    return min(1.0, sum(math.exp(lp(x)) for x in range(max(0, k - n2), min(n1, k) + 1) if lp(x) <= obs + 1e-9))


def analisa(escala, rotulo, casos_):
    por_partido = collections.defaultdict(collections.Counter)
    for c in casos_:
        if c["nivel"] in NIVEIS:
            por_partido[c["partido"]][c["nivel"]] += 1
    partidos = sorted({p for (_, p) in den} | set(por_partido))
    tabela = []
    for p in partidos:
        n = sum(por_partido[p].values())
        d = sum(den[(nv, p)] for nv in NIVEIS)
        if n or d:
            tabela.append(dict(partido=p, categoria=categoria(escala(p)), nota=escala(p), casos=n, mandatos=d,
                               por_mil=(1000 * n / d if d else None),
                               **{f"casos_{nv}": por_partido[p][nv] for nv in NIVEIS}))

    def soma(filtro, nv=None):
        niv = [nv] if nv else NIVEIS
        n = sum(t[f"casos_{x}"] for t in tabela if filtro(t) for x in niv)
        d = sum(den[(x, t["partido"])] for t in tabela if filtro(t) for x in niv)
        return n, d

    cats = []
    for cat in CATEGORIAS + ["Sem classificação"]:
        n, d = soma(lambda t: t["categoria"] == cat)
        cats.append(dict(categoria=cat, casos=n, mandatos=d, por_mil=(1000 * n / d if d else None)))
    blocos = {}
    for b in ("Esquerda ampla", "Centro", "Direita ampla"):
        n, d = soma(lambda t: BLOCO[t["categoria"]] == b)
        blocos[b] = dict(casos=n, mandatos=d, por_mil=(1000 * n / d if d else None))
    L, R = blocos["Esquerda ampla"], blocos["Direita ampla"]
    rr = (R["casos"] / R["mandatos"]) / (L["casos"] / L["mandatos"])
    se = math.sqrt(1 / R["casos"] + 1 / L["casos"])
    agregado = dict(razao_taxas=rr, ic95=[rr * math.exp(-1.96 * se), rr * math.exp(1.96 * se)],
                    p_fisher=fisher(L["casos"], L["mandatos"] - L["casos"], R["casos"], R["mandatos"] - R["casos"]))
    niveis, num, dd = [], 0.0, 0.0
    soma_a = soma_e = soma_v = 0.0
    for nv in NIVEIS:
        nl, dl = soma(lambda t: BLOCO[t["categoria"]] == "Esquerda ampla", nv)
        nr, dr = soma(lambda t: BLOCO[t["categoria"]] == "Direita ampla", nv)
        niveis.append(dict(nivel=nv, esq_casos=nl, esq_mandatos=dl, esq_por_mil=1000 * nl / dl if dl else None,
                           dir_casos=nr, dir_mandatos=dr, dir_por_mil=1000 * nr / dr if dr else None,
                           p_fisher=fisher(nl, dl - nl, nr, dr - nr) if dl and dr else None))
        if dl + dr:
            num += nr * (dl - nl) / (dl + dr)
            dd += nl * (dr - nr) / (dl + dr)
            N, m1, n1 = dl + dr, nl + nr, dl           # estratos 2x2: esquerda/direita x cassado/não
            soma_a += nl
            soma_e += n1 * m1 / N
            soma_v += n1 * (N - n1) * m1 * (N - m1) / (N * N * (N - 1))
    agregado["or_mantel_haenszel"] = num / dd if dd else None
    chi2 = (abs(soma_a - soma_e) - 0.5) ** 2 / soma_v if soma_v else None
    agregado["p_cmh"] = math.erfc(math.sqrt(chi2 / 2)) if chi2 is not None else None
    return dict(rotulo=rotulo, partidos=sorted(tabela, key=lambda x: -x["casos"]), categorias=cats, blocos=blocos,
                niveis=niveis, agregado=agregado)


def escala_uniao_media_simples(p):
    return 8.34 if p == "UNIÃO" else escala_2023(p)


principal = analisa(escala_2023, "Bolognesi et al. (2023); União Brasil pela edição de 2025", casos)
sens_2025 = analisa(escala_2025, "Bolognesi et al. (2025), média ponderada de 2022", casos)
sens_uniao = analisa(escala_uniao_media_simples, "União Brasil pela média simples de DEM e PSL (8,34)", casos)
sem_sup = [c for c in casos if c["origem"] != "eleição suplementar"]
sens_tse = analisa(escala_2023, "Prefeitos só pelo marcador do TSE (sem eleições suplementares)", sem_sup)

resumo = dict(
    gerado_em=datetime.date.today().isoformat(),
    totais=dict(
        casos_no_universo=len(casos),
        prefeitos_por_suplementar=sum(1 for c in casos if c["origem"] == "eleição suplementar"),
        prefeitos_so_marcador_tse=extra_marcados,
        altos_cargos=len(altos),
        altos_cargos_no_universo=sum(1 for a in altos if a["no_universo_normalizado"] == "sim"),
        eleitos_municipais_marcador_tse=len(tse_marcados),
        suplementares_sem_prefeito_localizado=sem_prefeito,
        suplementares_sem_prefeito_por_ciclo=dict(sorted(sem_ciclo.items())),
        mandatos_por_nivel={nv: sum(v for (n, _), v in den.items() if n == nv) for nv in NIVEIS}),
    prefeitos_por_ciclo=dict(sorted(collections.Counter(c["ano"] for c in casos if c["nivel"] == "prefeito").items())),
    prefeitos_eleitos_por_ciclo={str(c): sum(1 for (cc, _) in prefeito_eleito if cc == c) for c in CICLOS_PREFEITO},
    principal=principal, sens_2025=sens_2025, sens_uniao=sens_uniao, sens_tse=sens_tse)
(SAIDA / "resultados.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), encoding="utf-8")


def grava(nome, dados, campos):
    with open(SAIDA / nome, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(dados)


grava("eleitos_municipais_marcador_tse.csv", sorted(tse_marcados, key=lambda x: (x["ano"], x["partido_na_eleicao"])),
      ["ano", "cargo", "uf", "municipio", "nome", "partido_na_eleicao", "resultado", "marcador"])
grava("prefeitos_eleicao_suplementar.csv", suplementares,
      ["ciclo", "codigo_municipio", "prefeito_eleito", "partido_na_eleicao", "data_suplementar"])
grava("altos_cargos_classificados.csv", altos,
      ["ano", "nome", "cargo", "uf", "partido_na_eleicao", "partido_canonico", "categoria_2023",
       "tipo_de_perda", "motivo", "fonte", "no_universo_normalizado"])
grava("resultados_por_partido.csv", principal["partidos"],
      ["partido", "categoria", "nota", "casos", "mandatos", "por_mil"] + [f"casos_{n}" for n in NIVEIS])

print(json.dumps(resumo["totais"], ensure_ascii=False))
print(resumo["prefeitos_por_ciclo"], resumo["prefeitos_eleitos_por_ciclo"])
for s in (principal, sens_2025, sens_uniao, sens_tse):
    print(s["rotulo"])
    print(" ", s["blocos"])
    print(" ", s["agregado"])
for n in principal["niveis"]:
    print(n)
