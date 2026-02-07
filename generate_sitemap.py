#!/usr/bin/env python3
"""
Gerador de sitemap.xml estático.
Roda via scheduler ou manualmente para atualizar o sitemap.
Gera o arquivo em /www/wwwroot/scoutdados.com.br/sitemap.xml
"""
import sys
from pathlib import Path
from datetime import datetime

# Caminho do projeto
PROJECT_ROOT = Path(__file__).parent
SITE_ROOT = PROJECT_ROOT
BASE_URL = "https://scoutdados.com.br"

PAGES = [
    {"loc": "/", "changefreq": "daily", "priority": "1.0"},
    {"loc": "/brasileirao", "changefreq": "daily", "priority": "0.9"},
    {"loc": "/dashboard", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/escalacao", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/confrontos", "changefreq": "daily", "priority": "0.9"},
    {"loc": "/mercado", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/scouts", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/historico", "changefreq": "weekly", "priority": "0.6"},
    {"loc": "/estatisticas", "changefreq": "daily", "priority": "0.7"},
    {"loc": "/sobre", "changefreq": "monthly", "priority": "0.3"},
    {"loc": "/privacidade", "changefreq": "monthly", "priority": "0.2"},
    {"loc": "/termos", "changefreq": "monthly", "priority": "0.2"},
]


def generate_sitemap() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    
    urls_xml = ""
    for page in PAGES:
        urls_xml += f"""  <url>
    <loc>{BASE_URL}{page['loc']}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{page['changefreq']}</changefreq>
    <priority>{page['priority']}</priority>
  </url>\n"""
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}</urlset>"""


def main():
    sitemap = generate_sitemap()
    output_path = SITE_ROOT / "sitemap.xml"
    output_path.write_text(sitemap, encoding="utf-8")
    print(f"Sitemap gerado: {output_path} ({len(PAGES)} URLs)")


if __name__ == "__main__":
    main()
