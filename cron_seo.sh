#!/bin/bash

# Script de automação para atualização de SEO/SSG
# Adicione este script ao crontab para rodar periodicamente (ex: semanalmente)

echo "Iniciando atualização de SEO..."
date

# Navegar para o diretório do frontend
cd /www/wwwroot/scoutdados.com.br/frontend

# Rodar o script de pré-renderização
# Isso vai atualizar os arquivos HTML em dist/ com o conteúdo mais recente
echo "Executando prerender.mjs..."
/usr/bin/node prerender.mjs

echo "Atualização concluída!"
