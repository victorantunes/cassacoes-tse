"""Gera index.html (GitHub Pages) a partir de data/resultados.json e dos CSVs em data/.

Uso: python scripts/03_gerar_site.py
"""
import csv
import html
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from partidos import BOLOGNESI_2023, BOLOGNESI_2025, PRD_2023, PRD_2025, UNIAO_2025, categoria  # noqa: E402

R = json.loads((RAIZ / "data" / "resultados.json").read_text(encoding="utf-8"))
P, S25, SUN, STSE, T = R["principal"], R["sens_2025"], R["sens_uniao"], R["sens_tse"], R["totais"]
ALTOS = list(csv.DictReader(open(RAIZ / "data" / "altos_cargos_classificados.csv", encoding="utf-8-sig"), delimiter=";"))
MUNIC = list(csv.DictReader(open(RAIZ / "data" / "eleitos_municipais_marcador_tse.csv", encoding="utf-8-sig"), delimiter=";"))

e = html.escape

NOME_EXIBIDO = {"MDB": "MDB (PMDB)", "DEM": "DEM (PFL)", "Progressistas": "Progressistas (PP, PPB)", "PR": "PR (PL)",
                "PRB": "PRB (Republicanos)", "UNIÃO": "União Brasil", "SDD": "SDD (Solidariedade)", "PPS": "PPS (Cidadania)",
                "PTC": "PTC (Agir)", "PMN": "PMN (Mobiliza)", "Avante": "Avante (PT do B)", "DC": "DC (PSDC)", "Podemos": "Podemos (PTN)"}


def nome(p):
    return NOME_EXIBIDO.get(p, p)


def n(x, casas=0):
    if x is None:
        return "—"
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x):
    return n(100 * x, 0) + "%"


def p_txt(p):
    return "p < 0,001" if p < 0.001 else "p = " + n(p, 2)


ESQ, CEN, DIR = P["blocos"]["Esquerda ampla"], P["blocos"]["Centro"], P["blocos"]["Direita ampla"]
AG = P["agregado"]
NOMES_NIVEL = {"prefeito": "Prefeitos", "deputado": "Deputados federais", "senador": "Senadores", "governador": "Governadores"}

# ---------------------------------------------------------------- tabelas
def tabela_classificacao():
    linhas = []
    cats = {}
    for p, nota in BOLOGNESI_2023.items():
        cats.setdefault(categoria(nota), []).append((p, nota))
    cats.setdefault(categoria(UNIAO_2025), []).append(("União Brasil*", UNIAO_2025))
    cats.setdefault(categoria(PRD_2023), []).append(("PRD†", PRD_2023))
    faixas = {"Extrema-esquerda": "0 a 1,50", "Esquerda": "1,51 a 3,00", "Centro-esquerda": "3,01 a 4,49", "Centro": "4,50 a 5,50",
              "Centro-direita": "5,51 a 7,00", "Direita": "7,01 a 8,50", "Extrema-direita": "8,51 a 10"}
    for c in faixas:
        itens = sorted(cats.get(c, []), key=lambda x: x[1])
        linhas.append(f"<tr><th scope='row'>{c}</th><td>{faixas[c]}</td><td>" +
                      ", ".join(f"{e(p)} ({n(v, 2)})" for p, v in itens) + "</td></tr>")
    return ("<div class='rolagem'><table><thead><tr><th>Categoria</th><th>Faixa da média</th><th>Partidos (média)</th></tr></thead><tbody>"
            + "".join(linhas) + "</tbody></table></div>")


def barras(linhas, maximo, unidade="", casas=1):
    out = ["<ul class='barras'>"]
    for rotulo, valor, extra in linhas:
        w = 0 if not valor else max(1.5, 100 * valor / maximo)
        out.append(f"<li><span class='rot'>{e(rotulo)}</span><span class='trilho'><span class='barra' style='width:{w:.1f}%'></span></span>"
                   f"<span class='val'>{n(valor, casas)}{unidade}<small>{e(extra)}</small></span></li>")
    out.append("</ul>")
    return "".join(out)


def tabela_partidos():
    linhas = []
    for x in P["partidos"]:
        if not x["casos"]:
            continue
        pouco = " class='raro'" if x["casos"] < 5 else ""
        linhas.append(
            f"<tr{pouco}><th scope='row'>{e(nome(x['partido']))}</th><td>{e(x['categoria'])}</td><td data-v='{x['nota'] or 0}'>{n(x['nota'], 2)}</td>"
            f"<td data-v='{x['casos']}'>{n(x['casos'])}</td><td data-v='{x['casos_prefeito']}'>{n(x['casos_prefeito'])}</td>"
            f"<td data-v='{x['casos_deputado']}'>{n(x['casos_deputado'])}</td><td data-v='{x['casos_senador']}'>{n(x['casos_senador'])}</td>"
            f"<td data-v='{x['casos_governador']}'>{n(x['casos_governador'])}</td><td data-v='{x['mandatos']}'>{n(x['mandatos'])}</td>"
            f"<td data-v='{x['por_mil'] or 0}'>{n(x['por_mil'], 1)}</td></tr>")
    cab = ["Partido", "Categoria", "Nota", "Casos", "Prefeitos", "Dep. federais", "Senadores", "Governadores", "Mandatos eleitos", "Casos por mil"]
    return ("<div class='rolagem'><table class='ordenavel'><thead><tr>" + "".join(f"<th>{c}</th>" for c in cab) + "</tr></thead><tbody>"
            + "".join(linhas) + "</tbody></table></div>")


def tabela_categorias(res):
    linhas = []
    for c in res["categorias"]:
        if not c["mandatos"]:
            continue
        linhas.append(f"<tr><th scope='row'>{e(c['categoria'])}</th><td>{n(c['casos'])}</td><td>{n(c['mandatos'])}</td><td>{n(c['por_mil'], 1)}</td></tr>")
    return ("<div class='rolagem'><table><thead><tr><th>Categoria</th><th>Casos</th><th>Mandatos eleitos</th><th>Casos por mil</th></tr></thead><tbody>"
            + "".join(linhas) + "</tbody></table></div>")


def tabela_niveis():
    linhas = []
    for x in P["niveis"]:
        linhas.append(f"<tr><th scope='row'>{NOMES_NIVEL[x['nivel']]}</th><td>{n(x['esq_casos'])} / {n(x['esq_mandatos'])}</td><td>{n(x['esq_por_mil'], 1)}</td>"
                      f"<td>{n(x['dir_casos'])} / {n(x['dir_mandatos'])}</td><td>{n(x['dir_por_mil'], 1)}</td><td>{n(x['p_fisher'], 2)}</td></tr>")
    return ("<div class='rolagem'><table><thead><tr><th>Cargo</th><th>Esquerda ampla: casos / mandatos</th><th>Por mil</th>"
            "<th>Direita ampla: casos / mandatos</th><th>Por mil</th><th>p (Fisher)</th></tr></thead><tbody>" + "".join(linhas) + "</tbody></table></div>")


def tabela_sensibilidade():
    linhas = []
    for res in (P, S25, SUN, STSE):
        b, a = res["blocos"], res["agregado"]
        ic = a["ic95"]
        linhas.append(f"<tr><th scope='row'>{e(res['rotulo'])}</th><td>{n(b['Esquerda ampla']['por_mil'], 1)}</td><td>{n(b['Direita ampla']['por_mil'], 1)}</td>"
                      f"<td>{n(a['razao_taxas'], 2)} ({n(ic[0], 2)} a {n(ic[1], 2)})</td><td>{n(a['p_fisher'], 3)}</td>"
                      f"<td>{n(a['or_mantel_haenszel'], 2)}</td><td>{n(a['p_cmh'], 3)}</td></tr>")
    return ("<div class='rolagem'><table><thead><tr><th>Cenário</th><th>Esquerda ampla (por mil)</th><th>Direita ampla (por mil)</th>"
            "<th>Razão de taxas (IC 95%)</th><th>p (Fisher)</th><th>OR Mantel-Haenszel</th><th>p (CMH)</th></tr></thead><tbody>"
            + "".join(linhas) + "</tbody></table></div>")


def tabela_altos():
    linhas = []
    for a in ALTOS:
        linhas.append(f"<tr><td>{a['ano']}</td><th scope='row'>{e(a['nome'])}</th><td>{e(a['cargo'])}/{e(a['uf'])}</td><td>{e(a['partido_na_eleicao'])}</td>"
                      f"<td>{e(a['categoria_2023'])}</td><td>{e(a['tipo_de_perda'])}: {e(a['motivo'])}</td></tr>")
    return ("<input type='search' id='filtro' placeholder='Filtrar por nome, partido ou cargo' aria-label='Filtrar a lista'>"
            "<div class='rolagem'><table id='lista-altos'><thead><tr><th>Ano</th><th>Nome</th><th>Cargo/UF</th><th>Partido</th><th>Categoria</th>"
            "<th>Instância e motivo</th></tr></thead><tbody>" + "".join(linhas) + "</tbody></table></div>")


# ---------------------------------------------------------------- gráficos
cats_graf = [(c["categoria"], c["por_mil"], f"{n(c['casos'])} casos")
             for c in P["categorias"] if c["mandatos"] > 100]
GRAF_CAT = barras(cats_graf, max(v for _, v, _ in cats_graf))
grandes = sorted([x for x in P["partidos"] if x["mandatos"] >= 1000], key=lambda x: -x["por_mil"])
GRAF_PART = barras([(nome(x["partido"]), x["por_mil"], f"{n(x['casos'])} casos") for x in grandes], max(x["por_mil"] for x in grandes))
top_abs = sorted([x for x in P["partidos"]], key=lambda x: -x["casos"])[:10]
GRAF_ABS = barras([(nome(x["partido"]), x["casos"], "") for x in top_abs], top_abs[0]["casos"], casas=0)

tot_part = sum(x["casos"] for x in P["partidos"])
vice_vereador = sum(1 for m in MUNIC if m["cargo"] in ("Vice-Prefeito", "Vereador"))
prefeitos_total = T["prefeitos_por_suplementar"] + T["prefeitos_so_marcador_tse"]
com_partido = prefeitos_total + vice_vereador + T["altos_cargos"]
sem_partido = T["suplementares_sem_prefeito_localizado"]
mdb = next(x for x in P["partidos"] if x["partido"] == "MDB")
ptb = next(x for x in P["partidos"] if x["partido"] == "PTB")
pt = next(x for x in P["partidos"] if x["partido"] == "PT")
psb = next(x for x in P["partidos"] if x["partido"] == "PSB")
psdb = next(x for x in P["partidos"] if x["partido"] == "PSDB")
nd = {x["nivel"]: x for x in P["niveis"]}
cic = R["prefeitos_por_ciclo"]
mand = T["mandatos_por_nivel"]

TEXTO = {
    "N_UNIVERSO": n(T["casos_no_universo"]), "N_MANDATOS": n(sum(mand.values())),
    "TAXA_TOTAL": n(1000 * T["casos_no_universo"] / sum(mand.values()), 1),
    "N_PREFEITOS": n(prefeitos_total), "N_SUP": n(T["prefeitos_por_suplementar"]), "N_MARC": n(T["prefeitos_so_marcador_tse"]),
    "N_SEMPARTIDO": n(sem_partido), "N_VV": n(vice_vereador), "N_ALTOS": n(T["altos_cargos"]), "N_COMPARTIDO": n(com_partido),
    "N_ALTOS_UNIV": n(T["altos_cargos_no_universo"]),
    "ESQ_N": n(ESQ["casos"]), "ESQ_D": n(ESQ["mandatos"]), "ESQ_T": n(ESQ["por_mil"], 1),
    "CEN_N": n(CEN["casos"]), "CEN_D": n(CEN["mandatos"]), "CEN_T": n(CEN["por_mil"], 1),
    "DIR_N": n(DIR["casos"]), "DIR_D": n(DIR["mandatos"]), "DIR_T": n(DIR["por_mil"], 1),
    "RR": n(AG["razao_taxas"], 2), "IC_A": n(AG["ic95"][0], 2), "IC_B": n(AG["ic95"][1], 2), "P_FISHER": n(AG["p_fisher"], 3),
    "OR_MH": n(AG["or_mantel_haenszel"], 2), "P_CMH": n(AG["p_cmh"], 2),
    "RR25": n(S25["agregado"]["razao_taxas"], 2), "P25": n(S25["agregado"]["p_fisher"], 3), "PCMH25": n(S25["agregado"]["p_cmh"], 2),
    "RRTSE": n(STSE["agregado"]["razao_taxas"], 2), "ICTSE_A": n(STSE["agregado"]["ic95"][0], 2), "ICTSE_B": n(STSE["agregado"]["ic95"][1], 2),
    "MDB_N": n(mdb["casos"]), "MDB_T": n(mdb["por_mil"], 1), "PTB_T": n(ptb["por_mil"], 1), "PT_T": n(pt["por_mil"], 1), "PSB_T": n(psb["por_mil"], 1),
    "PSDB_N": n(psdb["casos"]), "PSDB_T": n(psdb["por_mil"], 1),
    "PREF_E": n(nd["prefeito"]["esq_por_mil"], 1), "PREF_D": n(nd["prefeito"]["dir_por_mil"], 1), "PREF_P": n(nd["prefeito"]["p_fisher"], 2),
    "DEP_E": n(nd["deputado"]["esq_por_mil"], 1), "DEP_D": n(nd["deputado"]["dir_por_mil"], 1), "DEP_P": n(nd["deputado"]["p_fisher"], 2),
    "SEN_E": n(nd["senador"]["esq_por_mil"], 1), "SEN_D": n(nd["senador"]["dir_por_mil"], 1),
    "GOV_E": n(nd["governador"]["esq_por_mil"], 1), "GOV_D": n(nd["governador"]["dir_por_mil"], 1), "GOV_P": n(nd["governador"]["p_fisher"], 2),
    "MAND_PREF": n(mand["prefeito"]), "MAND_DEP": n(mand["deputado"]), "MAND_SEN": n(mand["senador"]), "MAND_GOV": n(mand["governador"]),
    "C2004": n(cic.get("2004", 0)), "C2008": n(cic.get("2008", 0)), "C2012": n(cic.get("2012", 0)), "C2016": n(cic.get("2016", 0)),
    "C2020": n(cic.get("2020", 0)), "C2024": n(cic.get("2024", 0)),
    "SEM2016": n(T["suplementares_sem_prefeito_por_ciclo"].get("2016", 0)), "SEM2020": n(T["suplementares_sem_prefeito_por_ciclo"].get("2020", 0)),
    "SEM2024": n(T["suplementares_sem_prefeito_por_ciclo"].get("2024", 0)),
    "PCT_MAIS": pct(AG["razao_taxas"] - 1),
    "GRANDE_TOP": f"{nome(grandes[0]['partido'])} ({n(grandes[0]['por_mil'], 1)} por mil)",
    "GRANDE_BOT": f"{nome(grandes[-1]['partido'])} ({n(grandes[-1]['por_mil'], 1)} por mil)",
    "PRD23": n(PRD_2023, 2), "PRD25": n(PRD_2025, 2), "CAT_PRD23": categoria(PRD_2023).lower(), "CAT_PRD25": categoria(PRD_2025).lower(),
    "DATA": R["gerado_em"],
    "TAB_CLASSIF": tabela_classificacao(), "TAB_PARTIDOS": tabela_partidos(), "TAB_CATEGORIAS": tabela_categorias(P),
    "TAB_NIVEIS": tabela_niveis(), "TAB_SENS": tabela_sensibilidade(), "TAB_ALTOS": tabela_altos(),
    "GRAF_CAT": GRAF_CAT, "GRAF_PART": GRAF_PART, "GRAF_ABS": GRAF_ABS,
    "N_MUNIC": n(len(MUNIC)),
}

modelo = (RAIZ / "scripts" / "modelo.html").read_text(encoding="utf-8")
for k, v in TEXTO.items():
    modelo = modelo.replace("{{" + k + "}}", v)
restantes = [t for t in set(__import__("re").findall(r"\{\{[A-Z0-9_]+\}\}", modelo))]
if restantes:
    raise SystemExit(f"Marcadores sem valor: {restantes}")
(RAIZ / "index.html").write_text(modelo, encoding="utf-8")
print("index.html gerado:", len(modelo), "caracteres")
