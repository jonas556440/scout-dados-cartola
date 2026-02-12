"""
Mapeamento Central de Times — Fonte Única de Verdade
=====================================================
Todos os módulos devem importar daqui em vez de manter cópias locais.

Atualizar a cada temporada com os 20 times da Série A.
Temporada atual: Brasileirão 2025 (Cartola 2026).
"""
from typing import Dict, Optional

# ── Times da Série A 2025 ──
# Formato: slug → {nome, abrev_cartola, id_cartola, id_fdo, id_apifootball}
SERIE_A_TIMES = {
    "atletico-mg":         {"nome": "Atlético-MG",         "abrev": "CAM", "cartola_id": 282,  "fdo_id": 1766, "af_id": 1062},
    "athletico-pr":        {"nome": "Athletico-PR",         "abrev": "CAP", "cartola_id": 293,  "fdo_id": 1768, "af_id": 134},
    "bahia":               {"nome": "Bahia",                "abrev": "BAH", "cartola_id": 265,  "fdo_id": 1777, "af_id": 118},
    "botafogo":            {"nome": "Botafogo",             "abrev": "BOT", "cartola_id": 263,  "fdo_id": 1770, "af_id": 120},
    "chapecoense":         {"nome": "Chapecoense",          "abrev": "CHA", "cartola_id": 315,  "fdo_id": 1772, "af_id": 132},
    "corinthians":         {"nome": "Corinthians",          "abrev": "COR", "cartola_id": 264,  "fdo_id": 1779, "af_id": 131},
    "coritiba":            {"nome": "Coritiba",             "abrev": "CFC", "cartola_id": 294,  "fdo_id": 4241, "af_id": 147},
    "cruzeiro":            {"nome": "Cruzeiro",             "abrev": "CRU", "cartola_id": 283,  "fdo_id": 1771, "af_id": 135},
    "flamengo":            {"nome": "Flamengo",             "abrev": "FLA", "cartola_id": 262,  "fdo_id": 1783, "af_id": 127},
    "fluminense":          {"nome": "Fluminense",           "abrev": "FLU", "cartola_id": 266,  "fdo_id": 1765, "af_id": 124},
    "gremio":              {"nome": "Grêmio",               "abrev": "GRE", "cartola_id": 284,  "fdo_id": 1767, "af_id": 130},
    "internacional":       {"nome": "Internacional",        "abrev": "INT", "cartola_id": 285,  "fdo_id": 6684, "af_id": 119},
    "mirassol":            {"nome": "Mirassol",             "abrev": "MIR", "cartola_id": 2305, "fdo_id": 4364, "af_id": 7848},
    "palmeiras":           {"nome": "Palmeiras",            "abrev": "PAL", "cartola_id": 275,  "fdo_id": 1769, "af_id": 121},
    "red-bull-bragantino": {"nome": "Red Bull Bragantino",  "abrev": "RBB", "cartola_id": 280,  "fdo_id": 4286, "af_id": 794},
    "remo":                {"nome": "Remo",                 "abrev": "REM", "cartola_id": 364,  "fdo_id": 4287, "af_id": 1198},
    "santos":              {"nome": "Santos",               "abrev": "SAN", "cartola_id": 277,  "fdo_id": 6685, "af_id": 128},
    "sao-paulo":           {"nome": "São Paulo",            "abrev": "SAO", "cartola_id": 276,  "fdo_id": 1776, "af_id": 126},
    "vasco":               {"nome": "Vasco",                "abrev": "VAS", "cartola_id": 267,  "fdo_id": 1780, "af_id": 133},
    "vitoria":             {"nome": "Vitória",              "abrev": "VIT", "cartola_id": 287,  "fdo_id": 1782, "af_id": 136},
}

# Aliases de slug (ex: "bragantino" → dados de "red-bull-bragantino")
SLUG_ALIASES = {
    "bragantino": "red-bull-bragantino",
}

# ── Mapeamento FDO (football-data.org) TLA → abreviação Cartola ──
# A FDO usa siglas próprias que diferem do Cartola em vários times.
FDO_TO_CARTOLA: Dict[str, str] = {
    "PAU": "SAO",   # São Paulo FC → SAO (FDO usa "PAU")
    "FBP": "GRE",   # Grêmio FB Porto-Alegrense → GRE (FDO usa "FBP")
    "SCI": "INT",    # Sport Club Internacional → INT (FDO usa "SCI")
    "CRE": "REM",    # Clube do Remo → REM (FDO usa "CRE")
    "ACM": "CAM",    # Atlético-MG → CAM (FDO pode usar "ACM")
    "ATH": "CAP",    # Athletico-PR → CAP (FDO/web_scraper usa "ATH")
    "SAO": "SAO",    # São Paulo (identidade, para mapeamento bidirecional)
    "GRE": "GRE",    # Grêmio (identidade)
    "INT": "INT",    # Internacional (identidade)
    "REM": "REM",    # Remo (identidade)
}

# ── Lookups derivados ──

def _build_lookups():
    slug_to_abrev = {}
    abrev_to_slug = {}
    cartola_id_to_slug = {}
    abrev_to_nome = {}

    for slug, info in SERIE_A_TIMES.items():
        abrev = info["abrev"]
        slug_to_abrev[slug] = abrev
        abrev_to_slug[abrev] = slug
        cartola_id_to_slug[info["cartola_id"]] = slug
        abrev_to_nome[abrev] = info["nome"]

    # Adicionar aliases
    for alias, canonical in SLUG_ALIASES.items():
        if canonical in SERIE_A_TIMES:
            slug_to_abrev[alias] = SERIE_A_TIMES[canonical]["abrev"]

    return slug_to_abrev, abrev_to_slug, cartola_id_to_slug, abrev_to_nome


SLUG_TO_ABREV, ABREV_TO_SLUG, CARTOLA_ID_TO_SLUG, ABREV_TO_NOME = _build_lookups()


# ── Funções utilitárias ──

def get_abrev(slug: str) -> Optional[str]:
    """Retorna abreviação Cartola a partir do slug (ex: 'flamengo' → 'FLA')."""
    return SLUG_TO_ABREV.get(slug.lower())


def get_slug(abrev: str) -> Optional[str]:
    """Retorna slug a partir da abreviação (ex: 'FLA' → 'flamengo')."""
    return ABREV_TO_SLUG.get(abrev.upper())


def get_nome(abrev: str) -> Optional[str]:
    """Retorna nome completo a partir da abreviação (ex: 'FLA' → 'Flamengo')."""
    return ABREV_TO_NOME.get(abrev.upper())


def normalize_fdo_sigla(fdo_tla: str) -> str:
    """
    Converte sigla da football-data.org para formato Cartola.
    Ex: 'PAU' → 'SAO', 'FBP' → 'GRE', 'SCI' → 'INT'.
    Se não há conversão necessária, retorna a sigla original.
    """
    return FDO_TO_CARTOLA.get(fdo_tla, fdo_tla)


def get_all_slugs() -> list:
    """Retorna lista de todos os slugs (sem aliases)."""
    return list(SERIE_A_TIMES.keys())


def get_all_abrevs() -> list:
    """Retorna lista de todas as abreviações Cartola."""
    return [info["abrev"] for info in SERIE_A_TIMES.values()]


# ── Lookups FDO (football-data.org) ──

def _build_fdo_lookups():
    """Constroi mapeamentos FDO ID → cartola_id e vice-versa."""
    fdo_to_cartola_id = {}  # fdo_id → cartola_id
    cartola_to_fdo_id = {}  # cartola_id → fdo_id
    fdo_to_abrev = {}       # fdo_id → abreviação Cartola
    for slug, info in SERIE_A_TIMES.items():
        fdo = info.get("fdo_id", 0)
        if fdo:
            fdo_to_cartola_id[fdo] = info["cartola_id"]
            cartola_to_fdo_id[info["cartola_id"]] = fdo
            fdo_to_abrev[fdo] = info["abrev"]
    return fdo_to_cartola_id, cartola_to_fdo_id, fdo_to_abrev


FDO_TO_CARTOLA_ID, CARTOLA_TO_FDO_ID, FDO_TO_ABREV = _build_fdo_lookups()


def get_fdo_id(cartola_id: int) -> Optional[int]:
    """Retorna FDO team ID a partir do cartola_id."""
    return CARTOLA_TO_FDO_ID.get(cartola_id)


def get_cartola_id_from_fdo(fdo_id: int) -> Optional[int]:
    """Retorna cartola_id a partir do FDO team ID."""
    return FDO_TO_CARTOLA_ID.get(fdo_id)


def get_abrev_from_fdo(fdo_id: int) -> Optional[str]:
    """Retorna abreviação Cartola a partir do FDO team ID."""
    return FDO_TO_ABREV.get(fdo_id)
