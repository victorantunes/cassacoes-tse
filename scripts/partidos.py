"""Classificação ideológica dos partidos e agrupamento de siglas por sucessor."""

# Bolognesi, Ribeiro e Codato (2023), Dados 66(2), Tabela 1: média de 2018, escala 0-10.
BOLOGNESI_2023 = {
    "PSTU": 0.51, "PCO": 0.61, "PCB": 0.91, "PSOL": 1.28, "PCdoB": 1.92, "PT": 2.97,
    "PDT": 3.92, "PSB": 4.05, "Rede": 4.77, "PPS": 4.92, "PV": 5.29, "PTB": 6.10,
    "Avante": 6.32, "SDD": 6.50, "PMN": 6.88, "PMB": 6.90, "PHS": 6.96, "MDB": 7.01,
    "PSD": 7.09, "PSDB": 7.11, "Podemos": 7.24, "PPL": 7.27, "PRTB": 7.45, "Pros": 7.47,
    "PRP": 7.59, "PRB": 7.78, "PR": 7.78, "PTC": 7.86, "DC": 8.11, "PSL": 8.11,
    "Novo": 8.13, "Progressistas": 8.20, "PSC": 8.33, "Patriota": 8.55, "DEM": 8.57,
}

# O União Brasil (DEM + PSL, 2022) não está no artigo de 2023. Usa-se a média ponderada de 2022 de
# Bolognesi, Ribeiro, Codato e Silva (2025), Opinião Pública 31, e31120, Tabela 1.
UNIAO_2025 = 8.749

# Bolognesi et al. (2025), Tabela 1, coluna "média ponderada" (rodada de 2022).
BOLOGNESI_2025 = {
    "PSTU": 0.525, "PCO": 0.566, "PCB": 0.711, "PSOL": 1.453, "UP": 1.679, "PCdoB": 1.834,
    "PT": 2.761, "PSB": 3.699, "Rede": 3.802, "PDT": 3.977, "PV": 4.245, "SDD": 6.193,
    "PPS": 6.358, "Avante": 6.667, "MDB": 6.698, "PMN": 6.945, "PSDB": 6.966, "PSD": 7.151,
    "PMB": 7.512, "Podemos": 7.666, "Pros": 7.677, "PRTB": 7.718, "PTC": 7.780, "PTB": 7.955,
    "Progressistas": 8.398, "DC": 8.460, "PRB": 8.584, "PSC": 8.666, "UNIÃO": 8.749,
    "Patriota": 8.862, "Novo": 8.934, "PR": 9.068,
}

# Sigla do TSE (maiúscula) -> nome do partido sucessor usado nas tabelas acima.
SUCESSOR = {
    "PMDB": "MDB", "MDB": "MDB", "PFL": "DEM", "DEM": "DEM", "PP": "Progressistas",
    "PPB": "Progressistas", "PPR": "Progressistas", "PDS": "Progressistas",
    "PROGRESSISTAS": "Progressistas", "PL": "PR", "PR": "PR", "PST": "PR", "PRONA": "PR",
    "PC DO B": "PCdoB", "PCDOB": "PCdoB", "PT DO B": "Avante", "AVANTE": "Avante",
    "PODE": "Podemos", "PODEMOS": "Podemos", "PTN": "Podemos", "PSDC": "DC", "DC": "DC",
    "SD": "SDD", "SOLIDARIEDADE": "SDD", "REPUBLICANOS": "PRB", "PRB": "PRB", "PMR": "PRB",
    "MOBILIZA": "PMN", "PMN": "PMN", "AGIR": "PTC", "PTC": "PTC", "PRN": "PTC",
    "PATRIOTA": "Patriota", "PEN": "Patriota", "PROS": "Pros", "PPS": "PPS",
    "CIDADANIA": "PPS", "PSD": "PSD", "PSDB": "PSDB", "PSB": "PSB", "PDT": "PDT",
    "PT": "PT", "PTB": "PTB", "PAN": "PTB", "PV": "PV", "PSC": "PSC", "PRTB": "PRTB",
    "PHS": "PHS", "PSN": "PHS", "PRP": "PRP", "PSL": "PSL", "PPL": "PPL", "PMB": "PMB",
    "PSTU": "PSTU", "PCO": "PCO", "PCB": "PCB", "PSOL": "PSOL", "NOVO": "Novo",
    "REDE": "Rede", "UP": "UP", "PRD": "PRD",
}


def canon(sigla, ano=None):
    s = (sigla or "").strip().upper()
    if s.startswith("UNI") and s.endswith("O") and len(s) <= 7:
        return "UNIÃO"
    if s == "PSD" and ano is not None and ano < 2010:   # o PSD antigo foi incorporado ao PTB
        return "PTB"
    return SUCESSOR.get(s, s.title() if s else "")


def escala_2023(p):
    return UNIAO_2025 if p == "UNIÃO" else BOLOGNESI_2023.get(p)


def escala_2025(p):
    herdeiro = {"DEM": "UNIÃO", "PSL": "UNIÃO", "PHS": "Podemos", "PRP": "Patriota", "PPL": "PCdoB"}
    return BOLOGNESI_2025.get(herdeiro.get(p, p))


CATEGORIAS = ["Extrema-esquerda", "Esquerda", "Centro-esquerda", "Centro",
              "Centro-direita", "Direita", "Extrema-direita"]


def categoria(nota):
    if nota is None:
        return "Sem classificação"
    if nota <= 1.5:
        return "Extrema-esquerda"
    if nota <= 3.0:
        return "Esquerda"
    if nota <= 4.49:
        return "Centro-esquerda"
    if nota <= 5.5:
        return "Centro"
    if nota <= 7.0:
        return "Centro-direita"
    if nota <= 8.5:
        return "Direita"
    return "Extrema-direita"


BLOCO = {"Extrema-esquerda": "Esquerda ampla", "Esquerda": "Esquerda ampla",
         "Centro-esquerda": "Esquerda ampla", "Centro": "Centro",
         "Centro-direita": "Direita ampla", "Direita": "Direita ampla",
         "Extrema-direita": "Direita ampla", "Sem classificação": "Sem classificação"}
