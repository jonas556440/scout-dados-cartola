#!/bin/bash
set -e

# ============================================================
# deploy.sh — ScoutDados deploy
# Uso:  bash deploy.sh          → build frontend (OLS serve dist/ direto)
#       bash deploy.sh --full   → git pull + build + restart backend
# ============================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="/www/wwwroot/scoutdados.com.br"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DIST_DIR="$FRONTEND_DIR/dist"
OLS_CTL="/usr/local/lsws/bin/lswsctrl"

log()  { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
step() { echo -e "\n${CYAN}▶ $1${NC}"; }

echo ""
echo "═══════════════════════════════════════════"
echo "  ScoutDados — Deploy de Produção"
echo "═══════════════════════════════════════════"
echo ""

# ── 0. Git pull (se --full)
if [[ "$1" == "--full" ]]; then
    step "Git pull (origin/main)"
    cd "$PROJECT_ROOT"
    git pull origin main
    log "Código atualizado"
fi

# ── 1. Garantir que backend está rodando (necessário para SSG prerender)
step "Verificando backend (necessário para prerender SSG)"
if curl -sf http://localhost:8000/api/status > /dev/null 2>&1; then
    log "Backend respondendo em localhost:8000"
else
    warn "Backend não respondeu — reiniciando cartolafc-backend"
    systemctl restart cartolafc-backend 2>/dev/null || true
    sleep 3
    if curl -sf http://localhost:8000/api/status > /dev/null 2>&1; then
        log "Backend online após restart"
    else
        warn "Backend não disponível — build continuará sem prerender"
        export PRERENDER=false
    fi
fi

# ── 2. Instalar deps + Build frontend (com SSG prerender)
step "Build do frontend (Bun + Vite)"
cd "$FRONTEND_DIR"
export PATH="$PATH:/snap/bin"
bun install --frozen-lockfile 2>/dev/null || bun install

# Backup do dist atual para rollback
if [ -d "$DIST_DIR" ]; then
    step "Backup do dist anterior (rollback)"
    rm -rf "$DIST_DIR.bak"
    cp -r "$DIST_DIR" "$DIST_DIR.bak"
    log "Backup criado: $DIST_DIR.bak"
fi

# Build com rollback automático se falhar
if ! bun run build; then
    err_msg="Build falhou!"
    if [ -d "$DIST_DIR.bak" ]; then
        echo -e "${RED}❌ $err_msg Restaurando backup...${NC}"
        rm -rf "$DIST_DIR"
        mv "$DIST_DIR.bak" "$DIST_DIR"
        echo -e "${YELLOW}⚠️  Rollback aplicado — versão anterior restaurada${NC}"
        exit 1
    fi
    err "$err_msg"
fi
log "Build concluído → $DIST_DIR"

# ── 2b. SSG Pre-render (gera HTML estático com dados para SEO)
if [[ "$PRERENDER" != "false" ]]; then
    step "SSG Pre-render (Puppeteer + Chromium)"
    if node prerender.mjs; then
        PRERENDER_COUNT=$(find "$DIST_DIR" -name "index.html" | wc -l)
        log "Páginas pré-renderizadas: $PRERENDER_COUNT"
    else
        warn "Prerender falhou — site funciona como SPA normal"
    fi
else
    warn "Prerender desabilitado (backend offline)"
fi

# ── 2. Verificar artefatos
step "Verificando artefatos do build"
[[ -f "$DIST_DIR/index.html" ]] || err "index.html não encontrado em $DIST_DIR"
JS_HASH=$(grep -oP 'index-[A-Za-z0-9_-]+\.js' "$DIST_DIR/index.html" | head -1)
CSS_HASH=$(grep -oP 'index-[A-Za-z0-9_-]+\.css' "$DIST_DIR/index.html" | head -1)
[[ -f "$DIST_DIR/assets/$JS_HASH" ]]  || err "JS bundle não encontrado: $JS_HASH"
[[ -f "$DIST_DIR/assets/$CSS_HASH" ]] || err "CSS bundle não encontrado: $CSS_HASH"
log "Artefatos OK: $JS_HASH + $CSS_HASH"

# ── 3. Reiniciar OpenLiteSpeed (docroot = frontend/dist, sem cópia)
step "Reiniciando OpenLiteSpeed"
if [[ -x "$OLS_CTL" ]]; then
    $OLS_CTL restart
    log "OpenLiteSpeed reiniciado"
else
    warn "lswsctrl não encontrado em $OLS_CTL — reinicie manualmente"
fi

# ── 4. (Opcional) Reiniciar backend
if [[ "$1" == "--full" ]]; then
    step "Reiniciando backend + scheduler"
    systemctl restart cartolafc-backend 2>/dev/null && log "cartolafc-backend reiniciado" || warn "cartolafc-backend não reiniciou"
    systemctl restart cartolafc-scheduler 2>/dev/null && log "cartolafc-scheduler reiniciado" || warn "cartolafc-scheduler não reiniciou"
fi

# ── 5. Verificação final
step "Verificação final"
echo "  Docroot:    $DIST_DIR (servido diretamente pelo OLS)"
echo "  index.html: $(grep -oP 'index-[A-Za-z0-9_-]+\.(js|css)' "$DIST_DIR/index.html" | tr '\n' ' ')"
echo "  assets/:    $(ls "$DIST_DIR/assets/" | tr '\n' ' ')"

echo ""
echo "═══════════════════════════════════════════"
log "Deploy concluído com sucesso!"
echo ""
echo "  Uso rápido (só frontend):  bash deploy.sh"
echo "  Deploy completo:           bash deploy.sh --full"
echo "═══════════════════════════════════════════"
