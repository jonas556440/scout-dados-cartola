/**
 * Mapeamento de abreviação do Cartola → slug da URL.
 * Deve ser mantido em sincronia com TEAM_SLUGS no api_server.py
 */
const ABREV_TO_SLUG: Record<string, string> = {
  CAM: "atletico-mg",
  CAP: "athletico-pr",
  BAH: "bahia",
  BOT: "botafogo",
  CEA: "ceara",
  COR: "corinthians",
  CRU: "cruzeiro",
  FLA: "flamengo",
  FLU: "fluminense",
  FOR: "fortaleza",
  GRE: "gremio",
  INT: "internacional",
  JUV: "juventude",
  MIR: "mirassol",
  PAL: "palmeiras",
  RBB: "red-bull-bragantino",
  SAN: "santos",
  SAO: "sao-paulo",
  SPO: "sport",
  VAS: "vasco",
  VIT: "vitoria",
};

/**
 * Converte abreviação do Cartola (ex: "FLA") para slug de URL (ex: "flamengo").
 * Se não encontrar, gera slug a partir do nome em lowercase-kebab-case.
 */
export function getTeamSlug(abrev: string): string {
  return ABREV_TO_SLUG[abrev?.toUpperCase()] ?? abrev?.toLowerCase().replace(/\s+/g, "-") ?? "";
}
