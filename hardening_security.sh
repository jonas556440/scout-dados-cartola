#!/bin/bash
set -e

echo "🔒 Script de Hardening de Segurança - CartolaFC 2026"
echo "===================================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}❌ Execute como root: sudo bash hardening_security.sh${NC}"
   exit 1
fi

echo "📋 Este script vai:"
echo "  1. Atualizar dependências Python vulneráveis"
echo "  2. Implementar rate limiting na API"
echo "  3. Corrigir CORS para aceitar apenas domínios específicos"
echo "  4. Criar usuário dedicado (cartolafc)"
echo "  5. Configurar firewall (ufw)"
echo "  6. Adicionar headers de segurança"
echo "  7. Configurar backup automático"
echo "  8. Configurar logs seguros"
echo ""
read -p "Continuar? (s/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Operação cancelada."
    exit 1
fi

echo ""
echo "🔧 Iniciando hardening..."
echo ""

# ============================================
# 1. ATUALIZAR DEPENDÊNCIAS
# ============================================
echo -e "${YELLOW}[1/8] Atualizando dependências...${NC}"

cd /www/wwwroot/scoutdados.com.br
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate

pip install --upgrade pip -q
pip install --upgrade requests -q
pip install --upgrade fastapi -q
pip install --upgrade uvicorn -q
pip install --upgrade sqlalchemy -q
pip install slowapi -q  # Rate limiting

echo -e "${GREEN}✅ Dependências atualizadas${NC}"
echo ""

# ============================================
# 2. IMPLEMENTAR RATE LIMITING
# ============================================
echo -e "${YELLOW}[2/8] Implementando rate limiting...${NC}"

cat > /tmp/rate_limiter.py << 'RATE_EOF'
"""
Rate Limiter para FastAPI usando SlowAPI
Limita requisições por IP para prevenir DDoS
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Configurar limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour", "5000/day"],
    storage_uri="memory://"
)

def setup_rate_limiting(app):
    """Adiciona rate limiting à aplicação FastAPI"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    return limiter
RATE_EOF

mv /tmp/rate_limiter.py /www/wwwroot/scoutdados.com.br/src/utils/rate_limiter.py

echo -e "${GREEN}✅ Rate limiting configurado${NC}"
echo ""

# ============================================
# 3. CORRIGIR CORS
# ============================================
echo -e "${YELLOW}[3/8] Corrigindo CORS...${NC}"

read -p "Digite seu domínio (ex: scoutfutebol.com.br): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Domínio não pode estar vazio${NC}"
    exit 1
fi

# Backup do arquivo original
cp /www/wwwroot/scoutdados.com.br/api_server.py /www/wwwroot/scoutdados.com.br/api_server.py.backup

# Criar configuração segura de CORS
cat > /tmp/cors_config.txt << CORS_EOF
# ============ Configuração CORS Segura ============
ALLOWED_ORIGINS = [
    "https://${DOMAIN}",
    "https://www.${DOMAIN}",
    "http://localhost:5176",  # Dev apenas
    "http://127.0.0.1:5176",  # Dev apenas
]

# Se desenvolvimento
import os
if os.getenv("ENV") == "development":
    ALLOWED_ORIGINS.append("http://localhost:3000")
CORS_EOF

echo -e "${GREEN}✅ CORS configurado para: ${DOMAIN}${NC}"
echo -e "${YELLOW}⚠️  ATENÇÃO: Você precisa adicionar ALLOWED_ORIGINS ao api_server.py manualmente!${NC}"
echo -e "   Arquivo salvo em: /tmp/cors_config.txt"
echo ""

# ============================================
# 4. CRIAR USUÁRIO DEDICADO
# ============================================
echo -e "${YELLOW}[4/8] Criando usuário dedicado...${NC}"

# Criar usuário se não existir
if ! id "cartolafc" &>/dev/null; then
    useradd -r -s /bin/false -d /www/wwwroot/scoutdados.com.br cartolafc
    echo -e "${GREEN}✅ Usuário 'cartolafc' criado${NC}"
else
    echo -e "${YELLOW}⚠️  Usuário 'cartolafc' já existe${NC}"
fi

# Ajustar permissões
chown -R cartolafc:cartolafc /www/wwwroot/scoutdados.com.br
chmod 750 /www/wwwroot/scoutdados.com.br
chmod 640 /www/wwwroot/scoutdados.com.br/data/cartola.db

echo -e "${GREEN}✅ Permissões ajustadas${NC}"
echo ""

# ============================================
# 5. CONFIGURAR FIREWALL
# ============================================
echo -e "${YELLOW}[5/8] Configurando firewall (ufw)...${NC}"

# Instalar ufw se não tiver
apt-get install -y ufw -qq

# Configurar regras
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Permitir SSH (porta 22) - CRÍTICO!
ufw allow 22/tcp comment 'SSH'

# Permitir HTTP/HTTPS
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Ativar firewall
ufw --force enable

ufw status

echo -e "${GREEN}✅ Firewall configurado${NC}"
echo ""

# ============================================
# 6. ADICIONAR HEADERS DE SEGURANÇA
# ============================================
echo -e "${YELLOW}[6/8] Configurando headers de segurança...${NC}"

cat > /tmp/security_headers.py << 'HEADERS_EOF'
"""
Security Headers Middleware para FastAPI
Adiciona headers de segurança em todas as respostas
"""
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Adicionar headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response
HEADERS_EOF

mv /tmp/security_headers.py /www/wwwroot/scoutdados.com.br/src/utils/security_headers.py

echo -e "${GREEN}✅ Headers de segurança configurados${NC}"
echo ""

# ============================================
# 7. BACKUP AUTOMÁTICO
# ============================================
echo -e "${YELLOW}[7/8] Configurando backup automático...${NC}"

# Criar diretório de backups
mkdir -p /var/backups/cartolafc

# Script de backup
cat > /usr/local/bin/backup_cartolafc.sh << 'BACKUP_EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/cartolafc"
DATE=$(date +%Y%m%d_%H%M%S)
DB_PATH="/www/wwwroot/scoutdados.com.br/data/cartola.db"

# Criar backup do banco
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/cartola_$DATE.db'"

# Manter apenas últimos 30 dias
find "$BACKUP_DIR" -name "cartola_*.db" -mtime +30 -delete

# Comprimir backups antigos (mais de 7 dias)
find "$BACKUP_DIR" -name "cartola_*.db" -mtime +7 ! -name "*.gz" -exec gzip {} \;

echo "Backup criado: $BACKUP_DIR/cartola_$DATE.db"
BACKUP_EOF

chmod +x /usr/local/bin/backup_cartolafc.sh

# Cronjob diário às 3h
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup_cartolafc.sh >> /var/log/cartolafc_backup.log 2>&1") | crontab -

echo -e "${GREEN}✅ Backup automático configurado (diário às 3h)${NC}"
echo ""

# ============================================
# 8. LOGS SEGUROS
# ============================================
echo -e "${YELLOW}[8/8] Configurando logs seguros...${NC}"

# Criar diretório de logs
mkdir -p /var/log/cartolafc
chown cartolafc:cartolafc /var/log/cartolafc
chmod 750 /var/log/cartolafc

# Configurar logrotate
cat > /etc/logrotate.d/cartolafc << 'LOGROTATE_EOF'
/var/log/cartolafc/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
    create 0640 cartolafc cartolafc
    sharedscripts
    postrotate
        systemctl reload cartolafc-backend >/dev/null 2>&1 || true
    endscript
}
LOGROTATE_EOF

echo -e "${GREEN}✅ Logs configurados em /var/log/cartolafc${NC}"
echo ""

# ============================================
# RESUMO FINAL
# ============================================
echo ""
echo "==============================================="
echo -e "${GREEN}✅ Hardening de segurança concluído!${NC}"
echo "==============================================="
echo ""
echo "📋 Próximos passos MANUAIS:"
echo ""
echo "1. ⚠️  Editar api_server.py:"
echo "   - Adicionar ALLOWED_ORIGINS (ver /tmp/cors_config.txt)"
echo "   - Importar e usar rate_limiter"
echo "   - Importar e usar security_headers"
echo ""
echo "2. 🔄 Atualizar services systemd:"
echo "   - Mudar User=root para User=cartolafc"
echo "   - sudo systemctl daemon-reload"
echo "   - sudo systemctl restart cartolafc-*"
echo ""
echo "3. 🔐 Configurar HTTPS:"
echo "   sudo apt install certbot python3-certbot-apache"
echo "   sudo certbot --apache -d ${DOMAIN}"
echo ""
echo "4. 🧪 Testar segurança:"
echo "   - curl -I https://${DOMAIN}"
echo "   - nmap -sV \$(curl -s ifconfig.me)"
echo ""
echo "5. 📊 Monitorar logs:"
echo "   tail -f /var/log/cartolafc/api.log"
echo "   sudo journalctl -u cartolafc-backend -f"
echo ""
echo "⚠️  IMPORTANTE: Sistema ainda NÃO está 100% seguro!"
echo "   Complete os passos acima antes de produção."
echo ""
echo "📖 Documentação completa: /www/wwwroot/scoutdados.com.br/AUDITORIA_SEGURANCA.md"
echo ""
