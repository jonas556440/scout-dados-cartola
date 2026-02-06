#!/bin/bash
# Script para configurar e iniciar o projeto Cartola FC 2026 completo
# Backend Python + Frontend React

echo "🚀 Cartola FC 2026 - Setup Completo"
echo "=================================="

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/root/cartolafc2026"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# ============ Backend Setup ============
echo -e "\n${BLUE}📦 Configurando Backend...${NC}"

cd $PROJECT_DIR

# Instalar dependências Python
if [ -f "requirements.txt" ]; then
    echo "Instalando dependências Python..."
    pip install -q fastapi uvicorn pydantic 2>/dev/null
    pip install -r requirements.txt 2>/dev/null
    echo -e "${GREEN}✓ Dependências Python instaladas${NC}"
fi

# ============ Frontend Setup ============
echo -e "\n${BLUE}📱 Configurando Frontend...${NC}"

# Clonar repositório do frontend se não existir
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Clonando frontend de jonas556440/cartola-ai-pro..."
    git clone https://github.com/jonas556440/cartola-ai-pro.git $FRONTEND_DIR 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Frontend clonado com sucesso${NC}"
    else
        echo -e "${RED}✗ Erro ao clonar. Verificando alternativas...${NC}"
        # Criar estrutura mínima se clone falhar
        mkdir -p $FRONTEND_DIR
    fi
else
    echo "Frontend já existe em $FRONTEND_DIR"
fi

# Verificar se npm está instalado
if command -v npm &> /dev/null; then
    cd $FRONTEND_DIR
    
    if [ -f "package.json" ]; then
        echo "Instalando dependências Node.js..."
        npm install 2>/dev/null
        echo -e "${GREEN}✓ Dependências Node.js instaladas${NC}"
    fi
else
    echo -e "${YELLOW}⚠ npm não encontrado. Instale Node.js para o frontend.${NC}"
fi

# ============ Criar arquivo de configuração da API ============
echo -e "\n${BLUE}⚙️ Configurando conexão API...${NC}"

if [ -d "$FRONTEND_DIR/src" ]; then
    # Criar arquivo de configuração da API
    cat > "$FRONTEND_DIR/src/config/api.ts" << 'EOF'
/**
 * Configuração da API do Cartola FC 2026
 * Conexão com o backend Python
 */

// URL base da API (alterar em produção)
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Endpoints disponíveis
export const API_ENDPOINTS = {
    // Status
    status: '/api/status',
    
    // Mercado
    atletas: '/api/mercado/atletas',
    
    // Confrontos
    confrontos: '/api/confrontos',
    confrontosAnalise: '/api/confrontos/analise',
    
    // Escalação
    gerarEscalacao: '/api/escalacao/gerar',
    
    // Dashboard
    dashboard: '/api/dashboard',
} as const;

// Função helper para fazer requests
export async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });
    
    if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
}

// Funções específicas da API
export const cartolaApi = {
    // Buscar status do mercado
    getStatus: () => apiRequest(API_ENDPOINTS.status),
    
    // Buscar atletas
    getAtletas: (params?: { posicao?: string; precoMax?: number; limite?: number }) => {
        const searchParams = new URLSearchParams();
        if (params?.posicao) searchParams.set('posicao', params.posicao);
        if (params?.precoMax) searchParams.set('preco_max', params.precoMax.toString());
        if (params?.limite) searchParams.set('limite', params.limite.toString());
        
        const query = searchParams.toString();
        return apiRequest(`${API_ENDPOINTS.atletas}${query ? `?${query}` : ''}`);
    },
    
    // Buscar confrontos
    getConfrontos: (rodada?: number) => {
        const query = rodada ? `?rodada=${rodada}` : '';
        return apiRequest(`${API_ENDPOINTS.confrontos}${query}`);
    },
    
    // Buscar análise detalhada de confrontos
    getConfrontosAnalise: (rodada?: number) => {
        const query = rodada ? `?rodada=${rodada}` : '';
        return apiRequest(`${API_ENDPOINTS.confrontosAnalise}${query}`);
    },
    
    // Gerar escalação
    gerarEscalacao: (esquema: string = '4-4-2', cartoletas: number = 100) => {
        return apiRequest(`${API_ENDPOINTS.gerarEscalacao}?esquema=${esquema}&cartoletas=${cartoletas}`);
    },
    
    // Buscar dados do dashboard
    getDashboard: () => apiRequest(API_ENDPOINTS.dashboard),
};
EOF

    echo -e "${GREEN}✓ Configuração da API criada${NC}"
fi

# ============ Criar arquivo .env ============
if [ -d "$FRONTEND_DIR" ]; then
    echo "VITE_API_URL=http://localhost:8000" > "$FRONTEND_DIR/.env"
    echo -e "${GREEN}✓ Arquivo .env criado${NC}"
fi

# ============ Resumo ============
echo -e "\n${GREEN}=================================="
echo "✅ Setup concluído!"
echo "==================================${NC}"

echo -e "\n${YELLOW}Para iniciar:${NC}"
echo ""
echo "1. Backend (Terminal 1):"
echo "   cd $PROJECT_DIR"
echo "   python api_server.py"
echo "   # ou: uvicorn api_server:app --reload"
echo ""
echo "2. Frontend (Terminal 2):"
echo "   cd $FRONTEND_DIR"
echo "   npm run dev"
echo ""
echo -e "${BLUE}Acesse: http://localhost:5173${NC}"
echo ""
