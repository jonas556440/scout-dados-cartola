# Copilot Instructions - Cartola FC 2026

## Visão Geral da Arquitetura

Sistema fullstack para análise e escalação inteligente no Cartola FC, composto por:

| Componente | Tecnologia | Porta | Arquivo Principal |
|------------|------------|-------|-------------------|
| **Backend API** | FastAPI + Uvicorn | 8000 | `api_server.py` |
| **Frontend** | React + Vite + shadcn/ui | 5176 | `frontend/` |
| **CLI** | Rich + Click | - | `main.py` |
| **Scheduler** | APScheduler | - | `scheduler_service.py` |
| **Banco** | SQLite (SQLAlchemy) | - | `data/cartola.db` |

## Fluxo de Dados Principal

```
API Cartola Globo → CartolaAPI (src/api/) → MPVCalculator/TeamSelector (src/analysis/)
                                          ↓
                                    DatabaseManager (src/database/)
                                          ↓
                              api_server.py (FastAPI endpoints /api/*)
                                          ↓
                              Frontend (Vite proxy /api → :8000)
```

## Convenções Críticas

### Backend Python

- **Imports absolutos**: Sempre use `sys.path.append(str(Path(__file__).parent.parent))` no início de arquivos Python
  - Importações de `src/` e `config/` dependem do path sendo adicionado primeiro
  - Ver exemplos em [api_server.py](api_server.py), [main.py](main.py), [scheduler_service.py](scheduler_service.py)
- **Pydantic models**: Endpoints FastAPI retornam modelos compatíveis com `frontend/src/types/cartola.ts`
  - `PlayerResponse` ↔ `Player`, `ClubResponse` ↔ `Club`, `MatchResponse` ↔ `Match`
  - **Crítico**: Manter sincronia entre Pydantic e TypeScript ao adicionar campos
- **Cache da API**: `CartolaAPI._cache` com timeout de 5 minutos - evite chamadas repetidas
  - Cache por endpoint usando dict com chave `(endpoint, timestamp)`
- **Retry automático**: 3 tentativas com delay de 1s para API externa
  - **Não fazer retry em erros 4xx** (apenas 5xx e timeouts)
  - Ver `_make_request()` em [src/api/cartola_api.py](src/api/cartola_api.py)

```python
# Padrão de import no projeto
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.api.cartola_api import CartolaAPI
from config.settings import settings
```

### Frontend TypeScript

- **Path alias**: Use `@/` para imports (configurado em `tsconfig.json` e `vite.config.ts`)
- **API hooks**: Use hooks de `useCartolaApi.ts` com React Query, **não fetch direto**
  - `useAtletas()`, `useConfrontos()`, `useDashboard()` com staleTime/refetchInterval configurados
  - Todos os hooks retornam `{ data, isLoading, error, refetch }`
- **Tipos**: Interfaces em `src/types/cartola.ts` - manter sincronizado com Pydantic models
- **Proxy**: `/api/*` é proxiado para `localhost:8000` no dev (ver [vite.config.ts](frontend/vite.config.ts))
  - Em produção, usar reverse proxy (nginx/caddy)

```typescript
// Padrão de uso da API - SEMPRE via hooks
import { useAtletas, useConfrontos } from '@/hooks/useCartolaApi';

// ❌ ERRADO - não fazer fetch direto
fetch('/api/atletas')

// ✅ CORRETO
const { data: atletas, isLoading } = useAtletas({ posicao: 'ATA' });
```

### Algoritmos de Seleção (src/analysis/team_selector.py)

**Dois tipos de time por rodada com estratégias distintas:**

1. **Time Valorização**: Foca em jogadores C$3-6 (sweet spot confirmado por dados reais)
   - Exemplo rodada 1: Gabriel Menino C$6→C$10.77 (+79.5%), Léo Derik C$2→C$5.14 (+157%)
   - Fatores: Preço ideal (35%), Tendência (25%), Confronto (25%), Margem (15%)
   
2. **Time Pontuação**: Maximiza pontos considerando confrontos e mando de campo
   - Fatores: Qualidade jogador (30%), Confronto (35%), Posição (15%), Risco (20%)
   - Usa `MatchAnalyzer` para força ofensiva/defensiva, mando, chance SG, expectativa gols

**Estruturas de dados principais:**
- `AnaliseJogador` (dataclass): Contém `jogador`, `mpv`, `score`, `tendencia`, `risco`, `confronto`
- `TimeEscalado` (dataclass): Contém `titulares`, `capitao`, `reservas`, `analise_confrontos`
- `Confronto` (dataclass): Dados do jogo com força dos times, mando, forma recente

## Comandos de Desenvolvimento

```bash
# Backend (sempre do root do projeto)
pip install -r requirements.txt
uvicorn api_server:app --reload --port 8000

# Frontend (usa Bun, não npm)
cd frontend && bun install && bun run dev

# CLI interativo
python main.py
# Comandos CLI: status | confrontos | escalar | salvar | patrimonio | historico

# Testes
pytest                           # Backend (não implementado ainda)
cd frontend && bun run test      # Frontend (vitest)
```

## Serviços Systemd (Produção)

**Três serviços independentes rodando em background:**

```bash
# Ver status de todos
sudo systemctl status cartolafc-backend cartolafc-frontend cartolafc-scheduler

# Logs individuais
sudo journalctl -u cartolafc-backend -f      # API logs
sudo journalctl -u cartolafc-frontend -f     # Frontend logs
tail -f scheduler.log                         # Scheduler logs (arquivo local)

# Reiniciar após mudanças no código
sudo systemctl restart cartolafc-backend
sudo systemctl restart cartolafc-scheduler
sudo systemctl restart cartolafc-frontend
```

**Arquivos de configuração:**
- `/etc/systemd/system/cartolafc-backend.service` - API FastAPI
- `/etc/systemd/system/cartolafc-frontend.service` - React/Vite (modo preview)
- `/etc/systemd/system/cartolafc-scheduler.service` - Jobs agendados

## Endpoints API Principais

| Endpoint | Método | Descrição | Modelo Response |
|----------|--------|-----------|-----------------|
| `/api/status` | GET | Status do mercado e rodada atual | `MercadoStatus` |
| `/api/mercado/atletas` | GET | Lista atletas com análise MPV | `List[PlayerResponse]` |
| `/api/confrontos/analise` | GET | Análise de confrontos da rodada | `ConfrontosAnalise` |
| `/api/escalacao/gerar` | POST | Gera times otimizados (val + pont) | `EscalacaoResponse` |
| `/api/dashboard` | GET | Dados consolidados para dashboard | `DashboardStats` |
| `/api/atletas/{atleta_id}` | GET | Detalhes + histórico de um atleta | `PlayerDetailResponse` |

**Query params comuns:**
- `rodada` (int): Rodada específica (default: rodada atual)
- `posicao` (str): Filtrar por posição (GOL, ZAG, LAT, MEI, ATA, TEC)
- `preco_max` (float): Filtrar por preço máximo
- `limite` (int): Limitar número de resultados

## Estrutura de Dados Chave

**Backend (dataclasses):**
- `AnaliseJogador` (mpv_calculator.py): Análise individual com MPV, tendência, risco, confronto
- `TimeEscalado` (team_selector.py): Time completo com titulares (12), capitão (1), reservas (5)
- `Confronto` (match_analyzer.py): Dados do jogo com força ofensiva/defensiva, mando, forma

**Frontend (TypeScript interfaces):**
- `Player` (cartola.ts): Compatível com `PlayerResponse` Pydantic
- `Match` (cartola.ts): Compatível com `MatchResponse` Pydantic
- `Club` (cartola.ts): Compatível com `ClubResponse` Pydantic

**Integração crítica:** Ao adicionar campos no backend, adicione em ambos:
1. Pydantic model em [api_server.py](api_server.py)
2. Interface TypeScript em [frontend/src/types/cartola.ts](frontend/src/types/cartola.ts)

## Regras de Negócio Cartola

- **Orçamento**: 100 cartoletas iniciais (usa patrimônio acumulado após rodadas)
- **Formação**: 12 titulares = 1 GOL + 10 jogadores de linha + 1 TEC
- **Esquemas válidos**: `3-4-3`, `3-5-2`, `4-3-3`, `4-4-2`, `4-5-1`, `5-3-2`, `5-4-1`
  - Definidos em [config/settings.py](config/settings.py) - `ESQUEMAS_VALIDOS`
- **Capitão**: Recebe 1.5x pontos da rodada
- **Status jogador**: 7=Provável, 2=Dúvida, 3=Suspenso, 5=Contundido, 6=Nulo
  - API retorna `status_id`, converter para string no frontend
- **Limite por clube**: Máximo 5 jogadores do mesmo time (configurable)

## API Externa (Cartola Globo)

**Base URL**: `https://api.cartolafc.globo.com`

**Endpoints usados:**
- `/atletas/mercado` - Todos jogadores + preços + status (JSON ~2MB)
- `/mercado/status` - Status mercado (aberto/fechado) + rodada atual
- `/atletas/pontuados` - Scouts após rodada encerrar
- `/partidas/{rodada}` - Jogos da rodada para análise confrontos
- `/clubes` - Times brasileiros (id, nome, escudo)

**Rate limiting**: Sem limite oficial, mas usar cache de 5min para não sobrecarregar
**Timeout**: 15s (reduzido de 30s para melhor UX)
**Retry**: 3 tentativas com 1s de delay entre elas
