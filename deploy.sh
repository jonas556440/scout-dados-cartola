#!/bin/bash
set -e

# ============================================================
# deploy.sh — ScoutDados deploy (frontend + backend restart)
# Uso:  bash deploy.sh          → build + deploy frontend
#       bash deploy.sh --full   → git pull + build + deploy + restart backend
# ============================================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_ROOT="/www/wwwroot/scoutdados.com.br"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DIST_DIR="$FRONTEND_DIR/dist"
DOCROOT="$PROJECT_ROOT"          # OpenLiteSpeed serve o root do projeto
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

# ── 0. Git pull (se --full) ──────────────────────────────────
if [[ "$1" == "--full" ]]; then
    step "Git pull (origin/main)"
    cd "$PROJECT_ROOT"
    git pull origin main
    log "Código atualizado"
fi

# ── 1. Instalar deps + Build frontend ───────────────────────
step "Build do frontend (Bun + Vite)"
cd "$FRONTEND_DIR"
bun install --frozen-lockfile 2>/dev/null || bun install
bun run build
log "Build concluído → $DIST_DIR"

# ── 2. Verificar artefatos ──────────────────────────────────
step "Verificando artefatos do build"
[[ -f "$DIST_DIR/index.html" ]] || err "index.html não encontrado em $DIST_DIR"
JS_HASH=$(grep -oP 'index-[A-Za-z0-9_-]+\.js' "$DIST_DIR/index.html" | head -1)
CSS_HASH=$(grep -oP 'index-[A-Za-z0-9_-]+\.css' "$DIST_DIR/index.html" | head -1)
[[ -f "$DIST_DIR/assets/$JS_HASH" ]]  || err "JS bundle não encontrado: $JS_HASH"
[[ -f "$DIST_DIR/assets/$CSS_HASH" ]] || err "CSS bundle não encontrado: $CSS_HASH"
log "Artefatos OK: $JS_HASH + $CSS_HASH"

# ── 3. Deploy: copiar dist → docroot ────────────────────────
step "Publicando build no docroot"

# index.html
cp "$DIST_DIR/index.html" "$DOCROOT/index.html"

# assets (limpa antigos, copia novos)
rm -rf "$DOCROOT/assets"
cp -r "$DIST_DIR/assets" "$DOCROOT/assets"

# arquivos estáticos do public/
for f in .htaccess favicon.ico og-image.png og-image.svg robots.txt placeholder.svg; do
    [[ -f "$DIST_DIR/$f" ]] && cp "$DIST_DIR/$f" "$DOCROOT/$f"
done

log "Publicado no docroot: $DOCROOT"

# ── 4. Reiniciar OpenLiteSpeed ───────────────────────────────
step "Reiniciando OpenLiteSpeed"
if [[ -x "$OLS_CTL" ]]; then
    $OLS_CTL restart
    log "OpenLiteSpeed reiniciado"
else
    warn "lswsctrl não encontrado em $OLS_CTL — reinicie manualmente"
fi

# ── 5. (Opcional) Reiniciar backend ──────────────────────────
if [[ "$1" == "--full" ]]; then
    step "Reiniciando backend + scheduler"
    systemctl restart cartolafc-backend 2>/dev/null && log "cartolafc-backend reiniciado" || warn "cartolafc-backend não reiniciou"
    systemctl restart cartolafc-scheduler 2>/dev/null && log "cartolafc-scheduler reiniciado" || warn "cartolafc-scheduler não reiniciou"
fi

# ── 6. Verificação final ────────────────────────────────────
step "Verificação final"
echo "  index.html  → $(grep -oP 'index-[A-Za-z0-9_-]+\.(js|css)' "$DOCROOT/index.html" | tr '\n' ' ')"
echo "  assets/     → $(ls "$DOCROOT/assets/" | tr '\n' ' ')"

echo ""
echo "═══════════════════════════════════════════"
log "Deploy concluído com sucesso!"
echo ""
echo "  Uso rápido (só frontend):  bash deploy.sh"
echo "  Deploy completo:           bash deploy.sh --full"
echo "═══════════════════════════════════════════"
