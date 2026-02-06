"""
PATCH DE SEGURANÇA PARA api_server.py
=====================================

Este arquivo contém as modificações necessárias para tornar a API segura.

INSTRUÇÕES:
1. Adicione estas importações no topo do api_server.py
2. Configure ALLOWED_ORIGINS com seu domínio real
3. Adicione os middlewares ao app
4. Aplique os decorators @limiter.limit() nos endpoints críticos

"""

# ============================================
# 1. ADICIONAR IMPORTAÇÕES (após as existentes)
# ============================================

from src.utils.rate_limiter import limiter, setup_rate_limiting
from src.utils.security_headers import SecurityHeadersMiddleware
import os


# ============================================
# 2. CONFIGURAR ALLOWED_ORIGINS (substituir origins = ["*"])
# ============================================

# ❌ REMOVER ESTA LINHA VULNERÁVEL:
# origins = ["*"]

# ✅ ADICIONAR ISTO:
ALLOWED_ORIGINS = [
    "https://scoutfutebol.com.br",      # Seu domínio produção
    "https://www.scoutfutebol.com.br",  # WWW
]

# Apenas em desenvolvimento
if os.getenv("ENV") == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:3000",
    ])


# ============================================
# 3. ATUALIZAR CORS MIDDLEWARE (substituir a configuração atual)
# ============================================

# ❌ REMOVER:
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # VULNERÁVEL!
#     ...
# )

# ✅ ADICIONAR:
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,          # ← Apenas domínios específicos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Especificar métodos
    allow_headers=["*"],
    max_age=3600,  # Cache preflight por 1 hora
)


# ============================================
# 4. ADICIONAR MIDDLEWARES DE SEGURANÇA (após CORS)
# ============================================

# Rate Limiting
setup_rate_limiting(app)

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)


# ============================================
# 5. APLICAR RATE LIMIT NOS ENDPOINTS CRÍTICOS
# ============================================

# Exemplo: Endpoint de escalação (computacionalmente caro)
@app.post("/api/escalacao/gerar", response_model=EscalacaoResponse)
@limiter.limit("10/minute")  # ← Adicionar este decorator
async def gerar_escalacao(request: Request, params: EscalacaoParams):
    # ... código existente ...
    pass


# Exemplo: Endpoint de dashboard (muitas queries)
@app.get("/api/dashboard", response_model=DashboardStats)
@limiter.limit("30/minute")  # ← Adicionar este decorator
async def get_dashboard(request: Request):
    # ... código existente ...
    pass


# Endpoints de leitura simples (mais permissivos)
@app.get("/api/status", response_model=MercadoStatus)
@limiter.limit("100/minute")  # ← Mais requests permitidos
async def get_status(request: Request):
    # ... código existente ...
    pass


# ============================================
# 6. ADICIONAR VARIÁVEL DE AMBIENTE
# ============================================

# Criar arquivo .env na raiz do projeto:
"""
ENV=production
ALLOWED_ORIGINS=https://scoutfutebol.com.br,https://www.scoutfutebol.com.br
"""

# Carregar no início do api_server.py:
from dotenv import load_dotenv
load_dotenv()


# ============================================
# 7. ADICIONAR ENDPOINT DE HEALTH CHECK
# ============================================

@app.get("/health")
@limiter.limit("200/minute")
async def health_check(request: Request):
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


# ============================================
# EXEMPLO COMPLETO DE COMO DEVE FICAR O INÍCIO DO api_server.py
# ============================================

"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ... outros imports ...

from src.utils.rate_limiter import limiter, setup_rate_limiting
from src.utils.security_headers import SecurityHeadersMiddleware

# Configuração de CORS segura
ALLOWED_ORIGINS = [
    "https://scoutfutebol.com.br",
    "https://www.scoutfutebol.com.br",
]

if os.getenv("ENV") == "development":
    ALLOWED_ORIGINS.extend([
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ])

# Criar app
app = FastAPI(
    title="Cartola FC 2026 API",
    description="API REST para análise e escalação inteligente",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENV") == "development" else None,  # Desabilitar em prod
)

# Middlewares (ordem importa!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

setup_rate_limiting(app)
app.add_middleware(SecurityHeadersMiddleware)

# ... resto do código ...
"""


# ============================================
# CHECKLIST DE APLICAÇÃO
# ============================================

"""
[ ] 1. Instalar dependências: pip install slowapi python-dotenv
[ ] 2. Criar arquivos: rate_limiter.py, security_headers.py (feito pelo script)
[ ] 3. Criar .env com ENV=production e seu domínio
[ ] 4. Modificar api_server.py:
    [ ] Adicionar imports
    [ ] Substituir origins=["*"] por ALLOWED_ORIGINS
    [ ] Atualizar CORSMiddleware
    [ ] Adicionar middlewares de segurança
    [ ] Adicionar @limiter.limit() nos endpoints
[ ] 5. Testar localmente: ENV=development uvicorn api_server:app
[ ] 6. Reiniciar serviços: sudo systemctl restart cartolafc-backend
[ ] 7. Testar em produção: curl -I https://seudominio.com.br/api/status
"""


# ============================================
# TESTE RÁPIDO
# ============================================

"""
# Testar rate limiting (deve retornar 429 após 100 requests)
for i in {1..150}; do 
    curl -s https://seudominio.com.br/api/status | head -1
done

# Testar CORS (deve rejeitar origem não autorizada)
curl -H "Origin: https://sitemalicioso.com" \\
     -H "Access-Control-Request-Method: GET" \\
     -X OPTIONS https://seudominio.com.br/api/status -v

# Verificar headers de segurança
curl -I https://seudominio.com.br/api/status | grep -E "X-|Content-Security|Strict-Transport"
"""
