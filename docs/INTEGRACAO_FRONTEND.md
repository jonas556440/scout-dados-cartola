# 🔌 Integração Backend-Frontend Cartola FC 2026

## Visão Geral

Este documento explica como conectar o **backend Python** com o **frontend React** do repositório [jonas556440/cartola-ai-pro](https://github.com/jonas556440/cartola-ai-pro).

## ✅ Compatibilidade

| Frontend (TypeScript) | Backend (Python) | Status |
|----------------------|------------------|--------|
| `Player` interface | `AnaliseJogador` | ✅ 100% |
| `Team` interface | `TimeEscalado` | ✅ 100% |
| `Match` interface | `Confronto` | ✅ 100% |
| `Club` interface | `EstatisticasTime` | ✅ 100% |
| `DashboardStats` | API Response | ✅ 100% |

## 🚀 Quick Start

### 1. Iniciar o Backend (Terminal 1)

```bash
cd /root/cartolafc2026

# Opção A: Modo desenvolvimento
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

# Opção B: Modo simples
python api_server.py
```

### 2. Clonar e Iniciar o Frontend (Terminal 2)

```bash
# Clonar o frontend
git clone https://github.com/jonas556440/cartola-ai-pro /root/cartolafc2026/frontend

cd /root/cartolafc2026/frontend

# Configurar variável de ambiente
echo "VITE_API_URL=http://localhost:8000" > .env

# Instalar dependências
npm install

# Iniciar
npm run dev
```

### 3. Acessar

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📡 Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Health check |
| `/api/status` | GET | Status do mercado |
| `/api/mercado/atletas` | GET | Lista atletas com filtros |
| `/api/confrontos` | GET | Análise de confrontos |
| `/api/confrontos/analise` | GET | Análise detalhada (melhores/piores) |
| `/api/escalacao/gerar` | GET | Gera times otimizados |
| `/api/dashboard` | GET | Dados do dashboard |

### Parâmetros

#### `/api/mercado/atletas`
- `posicao`: GOL, LAT, ZAG, MEI, ATA, TEC
- `preco_max`: Preço máximo (float)
- `apenas_provaveis`: true/false (default: true)
- `limite`: Máximo de resultados (default: 100)

#### `/api/escalacao/gerar`
- `esquema`: 4-4-2, 4-3-3, 3-5-2, 4-5-1, etc.
- `cartoletas`: Budget disponível (default: 100)

## 🔧 Configuração do Frontend

### 1. Criar arquivo de configuração da API

Copie `/root/cartolafc2026/frontend_hooks/useCartolaApi.ts` para `frontend/src/hooks/`:

```typescript
// frontend/src/hooks/useCartolaApi.ts
import { useQuery } from '@tanstack/react-query';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useDashboard() {
    return useQuery({
        queryKey: ['dashboard'],
        queryFn: () => fetch(`${API_URL}/api/dashboard`).then(r => r.json()),
        staleTime: 1000 * 60 * 5,
    });
}

// ... outros hooks
```

### 2. Atualizar componentes

Substituir imports de mockData por chamadas à API:

```tsx
// ANTES (mockData)
import { mockDashboardStats } from "@/data/mockData";
const stats = mockDashboardStats;

// DEPOIS (API real)
import { useDashboard } from "@/hooks/useCartolaApi";
const { data: stats, isLoading, error } = useDashboard();
```

### 3. Configurar CORS (já configurado no backend)

O backend já inclui CORS configurado para aceitar requisições de qualquer origem:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📊 Mapeamento de Dados

### Player (Frontend) ↔ AnaliseJogador (Backend)

```typescript
// Frontend (TypeScript)
interface Player {
    id: number;
    nome: string;
    apelido: string;
    posicao: 'GOL' | 'LAT' | 'ZAG' | 'MEI' | 'ATA' | 'TEC';
    clubeId: number;
    clubeAbrev: string;
    preco: number;
    media: number;
    status: 'provavel' | 'duvida' | 'suspenso';
    tendencia?: number;
    potencial?: number;
    confronto?: object;  // NOVO: dados de confronto
}
```

```python
# Backend (Python)
@dataclass
class AnaliseJogador:
    atleta_id: int
    nome: str
    apelido: str
    posicao_abrev: str
    clube_id: int
    clube_abrev: str
    preco: float
    media: float
    mpv: float  # → potencial
    tendencia_valorizar: float  # → tendencia
```

### Match (Frontend) ↔ Confronto (Backend)

```typescript
// Frontend
interface Match {
    id: number;
    rodada: number;
    mandante: Club;
    visitante: Club;
    probabilidadeMandante?: number;
    probabilidadeEmpate?: number;
    probabilidadeVisitante?: number;
    // NOVO: dados de análise
    dificuldadeMandante?: string;
    chanceSgMandante?: number;
    expectativaGolsMandante?: number;
}
```

## 🎨 Recursos Extras do Backend

### 1. Análise de Confrontos

O backend fornece análise completa de cada partida:
- Probabilidade de vitória/empate/derrota
- Dificuldade do adversário (Muito Fácil → Muito Difícil)
- Chance de SG (Saldo de Gols)
- Expectativa de gols

### 2. Seleção Inteligente

O endpoint `/api/escalacao/gerar` retorna dois times:
- **Time Valorização**: Otimizado para valorização de preço
- **Time Pontuação**: Otimizado para pontuação alta

Ambos consideram:
- Análise de confrontos da rodada
- MPV (Melhor Pontuador por Valor)
- Tendência de valorização
- Budget disponível

### 3. Dados de Confronto por Jogador

Cada jogador retornado inclui dados do seu confronto:

```json
{
    "id": 123,
    "nome": "Jogador",
    "confronto": {
        "adversario": "FLA",
        "local": "casa",
        "dificuldade": "Fácil",
        "chance_sg": 0.45,
        "score": 8.5
    }
}
```

## 📁 Estrutura de Arquivos

```
/root/cartolafc2026/
├── api_server.py              # 🆕 Servidor FastAPI
├── setup_full.sh              # 🆕 Script de setup completo
├── requirements_api.txt       # 🆕 Dependências da API
├── frontend_hooks/
│   └── useCartolaApi.ts       # 🆕 Hooks React para a API
├── frontend_examples/
│   └── Dashboard.tsx          # 🆕 Exemplo de Dashboard
├── src/
│   ├── api/cartola_api.py     # Cliente da API Cartola
│   ├── analysis/
│   │   ├── mpv_calculator.py  # Calculadora MPV
│   │   ├── team_selector.py   # Seletor de times v3
│   │   ├── match_analyzer.py  # Analisador de confrontos
│   │   └── confrontos_analyzer.py
│   └── database/
│       └── db_manager.py      # Gerenciador do banco
└── frontend/                  # 🆕 Clone do repo React
    ├── src/
    │   ├── types/cartola.ts   # Interfaces TypeScript
    │   ├── pages/             # Dashboard, Escalacao, etc.
    │   ├── components/        # UI components
    │   └── data/mockData.ts   # → Substituir por API
    └── package.json
```

## ⚡ Performance

- **Cache**: Queries com `staleTime` de 5-10 minutos
- **Refetch**: Atualização automática configurável
- **Loading states**: Skeleton loaders inclusos
- **Error handling**: Tratamento de erros com fallback

## 🐛 Troubleshooting

### API não responde
```bash
# Verificar se o servidor está rodando
curl http://localhost:8000/

# Verificar logs
uvicorn api_server:app --reload --log-level debug
```

### CORS error
```bash
# O backend já tem CORS configurado
# Se precisar, adicione a origem específica:
allow_origins=["http://localhost:5173"]
```

### Dados não atualizando
```typescript
// Forçar refetch
const { refetch } = useDashboard();
refetch();
```

## 📝 Changelog

- **v3.0.0**: Integração completa com frontend React
- **v2.0.0**: Análise de confrontos
- **v1.0.0**: Backend básico com seleção de times
