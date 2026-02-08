#!/usr/bin/env python3
"""
Gerador dinâmico de sitemap.xml.
Inclui rotas estáticas do app + posts de blog (estáticos e auto-gerados).
Roda via scheduler ou manualmente para atualizar o sitemap.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
BASE_URL = "https://scoutdados.com.br"

# Rotas estáticas do frontend (devem espelhar App.tsx)
STATIC_PAGES = [
    {"loc": "/", "changefreq": "daily", "priority": "1.0"},
    {"loc": "/brasileirao", "changefreq": "daily", "priority": "0.9"},
    {"loc": "/confrontos", "changefreq": "daily", "priority": "0.9"},
    {"loc": "/dashboard", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/escalacao", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/mercado", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/scouts", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/estatisticas", "changefreq": "daily", "priority": "0.7"},
    {"loc": "/historico", "changefreq": "weekly", "priority": "0.6"},
    {"loc": "/blog", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/sobre", "changefreq": "monthly", "priority": "0.3"},
    {"loc": "/privacidade", "changefreq": "monthly", "priority": "0.2"},
    {"loc": "/termos", "changefreq": "monthly", "priority": "0.2"},
]

# Posts estáticos do frontend (espelham content/posts.ts)
STATIC_BLOG_SLUGS = [
    "monte-carlo-futebol",
    "xg-expected-goals",
    "classificacao-brasileirao-2026",
    "guia-cartola-fc-2026",
    "modelo-poisson-previsao-placares",
]


def _get_auto_blog_posts() -> list:
    """Lê posts auto-gerados em data/blog_posts/ e retorna URLs com datas."""
    posts_dir = PROJECT_ROOT / "data" / "blog_posts"
    entries = []
    if not posts_dir.exists():
        return entries
    for f in posts_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            slug = data.get("slug", f.stem)
            date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
            entries.append({"slug": slug, "date": date})
        except Exception:
            continue
    return entries


def _get_team_pages() -> list:
    """Gera URLs de páginas por time dinamicamente a partir dos dados disponíveis."""
    # Slugs canônicos dos times do Brasileirão 2026 (exclui aliases)
    team_slugs = [
        "atletico-mg", "athletico-pr", "bahia", "botafogo",
        "corinthians", "cruzeiro", "flamengo", "fluminense",
        "gremio", "internacional", "mirassol", "palmeiras",
        "santos", "sao-paulo", "vasco", "vitoria",
        "red-bull-bragantino", "chapecoense", "coritiba", "remo",
    ]
    
    # Tentar enriquecer com times da classificação real (JSON de cache)
    try:
        cache_file = PROJECT_ROOT / "data" / "stats_cache" / "classificacao.json"
        if cache_file.exists():
            import re
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            classificacao = data if isinstance(data, list) else data.get("classificacao", [])
            for t in classificacao:
                nome = t.get("time", "")
                # Gerar slug a partir do nome
                slug = nome.lower().strip()
                slug = slug.replace(" ", "-").replace(".", "")
                slug = re.sub(r"[^a-z0-9-]", "", slug)
                if slug and slug not in team_slugs:
                    team_slugs.append(slug)
    except Exception:
        pass  # Fallback para lista hardcoded
    
    return [{"slug": s} for s in team_slugs]


def _get_match_pages() -> list:
    """Lê páginas de jogos auto-geradas em data/match_pages/."""
    match_dir = PROJECT_ROOT / "data" / "match_pages"
    entries = []
    if not match_dir.exists():
        return entries
    for f in match_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            slug = data.get("slug", f.stem)
            date = data.get("date", data.get("data", datetime.now().strftime("%Y-%m-%d")))
            entries.append({"slug": slug, "date": date})
        except Exception:
            continue
    return entries


def generate_sitemap() -> str:
    today = datetime.now().strftime("%Y-%m-%d")

    urls = []

    # 1. Rotas estáticas
    for page in STATIC_PAGES:
        urls.append({
            "loc": f"{BASE_URL}{page['loc']}",
            "lastmod": today,
            "changefreq": page["changefreq"],
            "priority": page["priority"],
        })

    # 2. Blog posts estáticos
    for slug in STATIC_BLOG_SLUGS:
        urls.append({
            "loc": f"{BASE_URL}/blog/{slug}",
            "lastmod": today,
            "changefreq": "monthly",
            "priority": "0.6",
        })

    # 3. Blog posts auto-gerados
    for post in _get_auto_blog_posts():
        urls.append({
            "loc": f"{BASE_URL}/blog/{post['slug']}",
            "lastmod": post["date"],
            "changefreq": "weekly",
            "priority": "0.7",
        })

    # 4. Páginas por time
    for team in _get_team_pages():
        urls.append({
            "loc": f"{BASE_URL}/brasileirao/time/{team['slug']}",
            "lastmod": today,
            "changefreq": "daily",
            "priority": "0.8",
        })

    # 5. Páginas de jogos individuais
    for match in _get_match_pages():
        urls.append({
            "loc": f"{BASE_URL}/brasileirao/jogo/{match['slug']}",
            "lastmod": match.get("date", today),
            "changefreq": "weekly",
            "priority": "0.6",
        })

    # Deduplicar URLs por loc
    seen = set()
    unique_urls = []
    for u in urls:
        if u["loc"] not in seen:
            seen.add(u["loc"])
            unique_urls.append(u)
    urls = unique_urls

    # Gerar XML
    xml_entries = ""
    for u in urls:
        xml_entries += f"""  <url>
    <loc>{u['loc']}</loc>
    <lastmod>{u['lastmod']}</lastmod>
    <changefreq>{u['changefreq']}</changefreq>
    <priority>{u['priority']}</priority>
  </url>\n"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{xml_entries}</urlset>"""


def main():
    sitemap = generate_sitemap()
    # Escrever na raiz do projeto (servido pelo OLS como /sitemap.xml)
    output_path = PROJECT_ROOT / "sitemap.xml"
    output_path.write_text(sitemap, encoding="utf-8")
    
    # Também copiar para frontend/dist se existir (deploy já feito)
    dist_path = PROJECT_ROOT / "frontend" / "dist" / "sitemap.xml"
    if dist_path.parent.exists():
        dist_path.write_text(sitemap, encoding="utf-8")

    # Contar URLs por tipo
    static_count = len(STATIC_PAGES)
    blog_static = len(STATIC_BLOG_SLUGS)
    blog_auto = len(_get_auto_blog_posts())
    teams = len(_get_team_pages())
    matches = len(_get_match_pages())
    
    # Contar URLs no XML gerado
    total = sitemap.count("<url>")
    print(f"Sitemap gerado: {output_path} ({total} URLs)")
    print(f"  Rotas estáticas: {static_count} | Blog estático: {blog_static} | Blog auto: {blog_auto} | Times: {teams} | Jogos: {matches}")


if __name__ == "__main__":
    main()
