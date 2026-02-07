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
    """Gera URLs de páginas por time a partir dos times conhecidos."""
    teams_file = PROJECT_ROOT / "data" / "blog_posts"
    # Slugs dos 20 times do Brasileirão 2026
    team_slugs = [
        "atletico-mg", "athletico-pr", "bahia", "botafogo",
        "corinthians", "cruzeiro", "cuiaba", "flamengo",
        "fluminense", "fortaleza", "gremio", "internacional",
        "juventude", "mirassol", "palmeiras", "santos",
        "sao-paulo", "sport", "vasco", "vitoria",
    ]
    return [{"slug": s} for s in team_slugs]


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
    total = static_count + blog_static + blog_auto + teams
    print(f"Sitemap gerado: {output_path} ({total} URLs)")
    print(f"  Rotas estáticas: {static_count} | Blog estático: {blog_static} | Blog auto: {blog_auto} | Times: {teams}")


if __name__ == "__main__":
    main()
