#!/bin/bash
set -e

echo "🚀 Deploy Production - ScoutDados"
echo "================================="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Diretórios
PROJECT_ROOT="/root/cartolafc2026"
BLOG_DIR="$PROJECT_ROOT/blog"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DEPLOY_DIR="/var/www/scout"
SITE_DIR="$DEPLOY_DIR/site"
TOOLS_DIR="$DEPLOY_DIR/tools"

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}❌ Execute como root: sudo bash deploy_production.sh${NC}"
   exit 1
fi

echo "📋 Configurações:"
echo "  Blog:     $BLOG_DIR"
echo "  Frontend: $FRONTEND_DIR"
echo "  Deploy:   $DEPLOY_DIR"
echo ""

# Criar diretórios de deploy
echo "📁 Criando estrutura de deploy..."
mkdir -p "$SITE_DIR" "$TOOLS_DIR"
mkdir -p /var/log/scout

# Build do blog (Astro)
if [ -d "$BLOG_DIR" ]; then
    echo ""
    echo "🏗️  Buildando blog Astro..."
    cd "$BLOG_DIR"
    
    if [ ! -d "node_modules" ]; then
        echo "📦 Instalando dependências do blog..."
        npm install
    fi
    
    npm run build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Build do blog concluído${NC}"
        
        # Deploy do blog
        echo "📦 Copiando blog para $SITE_DIR..."
        rsync -av --delete dist/ "$SITE_DIR/"
        
        # Garantir permissões
        chown -R www-data:www-data "$SITE_DIR"
        chmod -R 755 "$SITE_DIR"
        
        echo -e "${GREEN}✅ Blog deployado${NC}"
    else
        echo -e "${RED}❌ Erro no build do blog${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Diretório do blog não encontrado: $BLOG_DIR${NC}"
    echo "   Execute setup_astro_blog.sh primeiro!"
    exit 1
fi

# Build do frontend (Vite React)
echo ""
echo "🏗️  Buildando frontend React..."
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências do frontend..."
    # Usar bun se disponível, senão npm
    if command -v bun &> /dev/null; then
        bun install
    else
        npm install
    fi
fi

# Build com base path /tools
if command -v bun &> /dev/null; then
    bun run build
else
    npm run build
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build do frontend concluído${NC}"
    
    # Deploy do frontend
    echo "📦 Copiando frontend para $TOOLS_DIR..."
    rsync -av --delete dist/ "$TOOLS_DIR/"
    
    # Garantir permissões
    chown -R www-data:www-data "$TOOLS_DIR"
    chmod -R 755 "$TOOLS_DIR"
    
    echo -e "${GREEN}✅ Frontend deployado${NC}"
else
    echo -e "${RED}❌ Erro no build do frontend${NC}"
    exit 1
fi

# Criar .htaccess para SPA (React Router)
cat > "$TOOLS_DIR/.htaccess" << 'HTACCESS'
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /tools/
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule . /tools/index.html [L]
</IfModule>
HTACCESS

# Verificar backend FastAPI
echo ""
echo "🔍 Verificando serviço FastAPI..."

if systemctl is-active --quiet scout-api 2>/dev/null; then
    echo "🔄 Reiniciando scout-api..."
    systemctl restart scout-api
    sleep 2
    
    if systemctl is-active --quiet scout-api; then
        echo -e "${GREEN}✅ scout-api rodando${NC}"
    else
        echo -e "${RED}❌ scout-api falhou ao reiniciar${NC}"
        journalctl -u scout-api -n 20 --no-pager
    fi
elif systemctl is-active --quiet cartolafc-backend 2>/dev/null; then
    echo "🔄 Reiniciando cartolafc-backend..."
    systemctl restart cartolafc-backend
    sleep 2
    
    if systemctl is-active --quiet cartolafc-backend; then
        echo -e "${GREEN}✅ cartolafc-backend rodando${NC}"
    else
        echo -e "${YELLOW}⚠️  cartolafc-backend com problemas${NC}"
        journalctl -u cartolafc-backend -n 20 --no-pager
    fi
else
    echo -e "${YELLOW}⚠️  Nenhum serviço FastAPI encontrado${NC}"
    echo "   Certifique-se de ter scout-api.service ou cartolafc-backend.service"
fi

# Recarregar Apache
echo ""
echo "🔄 Recarregando Apache..."
if systemctl is-active --quiet apache2; then
    systemctl reload apache2
    echo -e "${GREEN}✅ Apache recarregado${NC}"
else
    echo -e "${RED}❌ Apache não está rodando${NC}"
    exit 1
fi

# Testes de validação
echo ""
echo "🧪 Validando deploy..."

# Teste 1: Landing page
if curl -s -o /dev/null -w "%{http_code}" http://localhost:80/ | grep -q "200"; then
    echo -e "${GREEN}✅ Landing page (/) acessível${NC}"
else
    echo -e "${RED}❌ Landing page não acessível${NC}"
fi

# Teste 2: Tools
if curl -s -o /dev/null -w "%{http_code}" http://localhost:80/tools/ | grep -q "200"; then
    echo -e "${GREEN}✅ Tools (/tools) acessível${NC}"
else
    echo -e "${YELLOW}⚠️  Tools não acessível (pode estar OK se Apache não configurado)${NC}"
fi

# Teste 3: API
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs | grep -q "200"; then
    echo -e "${GREEN}✅ API (/api) acessível${NC}"
else
    echo -e "${YELLOW}⚠️  API não acessível diretamente (pode estar OK se proxiado)${NC}"
fi

# Resumo
echo ""
echo "═══════════════════════════════════════"
echo -e "${GREEN}✅ Deploy concluído com sucesso!${NC}"
echo "═══════════════════════════════════════"
echo ""
echo "📍 Estrutura deployada:"
echo "  / → $SITE_DIR (Astro SSG)"
echo "  /tools → $TOOLS_DIR (React SPA)"
echo "  /api → 127.0.0.1:8000 (FastAPI)"
echo ""
echo "📊 Uso de disco:"
du -sh "$SITE_DIR" "$TOOLS_DIR" 2>/dev/null || echo "  (não disponível)"
echo ""
echo "🔗 URLs de teste:"
echo "  Landing: http://localhost/"
echo "  Blog:    http://localhost/blog"
echo "  Tools:   http://localhost/tools"
echo "  API:     http://localhost/api/status"
echo ""
echo "📋 Próximos passos:"
echo "  1. Configure Apache (ver apache_production.conf)"
echo "  2. Configure SSL: sudo certbot --apache -d seudominio.com.br"
echo "  3. Teste em produção"
echo ""
echo "📖 Logs:"
echo "  sudo journalctl -u scout-api -f"
echo "  sudo tail -f /var/log/apache2/error.log"
echo ""
