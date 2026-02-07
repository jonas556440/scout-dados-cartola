# Copilot Instructions - ScoutDados.com.br

## Arquitetura

Portal de estatísticas de futebol (Cartola FC + Brasileirão). Monolito FastAPI + SPA React.

| Componente | Stack | Porta | Entrada |
|------------|-------|-------|---------|
| Backend API | FastAPI + Uvicorn | 8000 | `api_server.py` (~2000 linhas, monolítico — sem APIRouter) |
| Frontend | React 18 + Vite (SWC) + shadcn/ui + React Query 5 | 5176 | `frontend/` |
| Scheduler | APScheduler (BackgroundScheduler) | — | `scheduler_service.py` |
| CLI | Rich + Click | — | `main.py` |
| DB | SQLite + SQLAlchemy (WAL mode) | — | `data/cartola.db` |

**Fluxo de dados:** API Cartola Globo → `src/api/cartola_api.py` (requests síncrono, cache 5min, retry 3x) → `src/analysis/` (MPV, TeamSelector, ScorePredictor) → `api_server.py` (endpoints `/api/*`) → Frontend (proxy Vite `/api` → `:8000`)

**Produção:** OpenLiteSpeed serve estáticos do docroot (`/www/wwwroot/scoutdados.com.br/`). O build de `frontend/dist/` é copiado para o docroot via `deploy.sh`. 2 serviços systemd (`cartolafc-backend`, `cartolafc-scheduler`).

## Convenções Obrigatórias

### Python — Path hack obrigatório
Todo arquivo Python executável do root precisa deste preâmbulo **antes** de qualquer import de `src/` ou `config/`:
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))  # .parent se na raiz, .parent.parent se em subpasta
```

### Sincronia Pydantic ↔ TypeScript (3 arquivos sempre juntos)
Ao adicionar/alterar campos em responses da API, editar **os três** :
1. **Pydantic model** em `api_server.py` (ex: `PlayerResponse`, `MatchResponse`)
2. **Função converter** em `api_server.py` (`converter_atleta_para_response()` ou `converter_partida_para_response()`) — bridge entre dict cru da API Cartola → Pydantic model
3. **Interface TS** em `frontend/src/types/cartola.ts` (ex: `Player`, `Match`)

### Novo endpoint — Checklist completo
Ao criar endpoint no backend, completar **toda a cadeia**:
1. Endpoint em `api_server.py` (seguir padrão try/except com HTTPException 503 se API indisponível)
2. Path em `frontend/src/config/api.ts` → `API_ENDPOINTS`
3. Método no objeto `cartolaApi` (mesmo arquivo)
4. Hook React Query em `frontend/src/hooks/useCartolaApi.ts`
5. Tipo/interface em `frontend/src/types/cartola.ts`

### Frontend — API sempre via hooks
```typescript
// ✅ hooks React Query — frontend/src/hooks/useCartolaApi.ts
const { data, isLoading } = useAtletas({ posicao: 'ATA' });

// ❌ NUNCA fetch direto
fetch('/api/mercado/atletas');
```

### Frontend — Organização de componentes
- `components/ui/` — shadcn/ui primitives (Radix) — usar `cn()` de `@/lib/utils` para classes
- `components/cartola/` — componentes de domínio (PlayerCard, MatchCard, FormationDisplay)
- `components/layout/` — MainLayout (sidebar + conteúdo) e Sidebar
- `components/SEO.tsx` — wrapper Helmet para meta tags OG/Twitter
- Path alias `@/` → `frontend/src/`
- Ícones: sempre `lucide-react`
- Animações: `framer-motion` (motion.div com initial/animate)

### Frontend — Branding e navegação
- **Marca:** "ScoutDados" em toda a UI. "Cartola FC" é só nome de seção no menu
- **Logo:** quadrado verde com letra "S" (não usar ícone Trophy, não usar "C")
- **Sidebar:** 3 seções com headers (`🏆 Brasileirão`, `⚽ Cartola FC`, `📊 Análises`)
- **Nunca usar** "Cartola FC 2026" como título/marca do app

### Frontend — Blog
- Posts em `frontend/src/content/posts.ts` (array de objetos TSX, sem MDX)
- Páginas: `Blog.tsx` (lista) e `BlogPost.tsx` (individual por slug)
- Usa `react-markdown` para renderizar conteúdo
- Linguagem 100% estatística, disclaimer obrigatório em posts de previsão

### Frontend — Padrão de página
Cada página: default export, importa `MainLayout` diretamente (não há layout aninhado no router), usa `<SEO>` para meta tags, estados loading/error antes do conteúdo.

### Backend — Padrão de endpoint
Endpoints são funções **síncronas** (`def`, não `async def`). Usam instâncias globais singleton (`api`, `mpv_calc`, `team_selector`, etc.) criadas no module-load. Padrão recorrente:
```python
@app.get("/api/...")
def endpoint():
    try:
        mercado = api.get_mercado()
        if not mercado:
            raise HTTPException(status_code=503, detail="API Cartola indisponível")
        clubes = mercado.get("clubes", {})
        # ... lógica ...
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
```

### Resiliência
- `src/utils/cache.py`: `CircuitBreaker` por fonte + `@with_circuit_breaker("fonte")` decorator (async)
- `src/utils/rate_limiter.py`: slowapi, 200/min default, endpoints pesados 30/min
- `CartolaAPI` tem cache interno (dict, TTL 5min) separado do cache global

## Comandos de Desenvolvimento

```bash
# Backend (do root)
uvicorn api_server:app --reload --port 8000

# Frontend (usa Bun, NÃO npm/yarn)
cd frontend && bun install && bun run dev

# Testes
pytest tests/ -m smoke          # smoke tests (aceita 200 ou 503)
pytest tests/ -v                # todos
cd frontend && bun run test     # vitest

# Deploy produção (SEMPRE usar o script — nunca copiar manualmente)
bash deploy.sh          # só frontend: build + copia dist→docroot + restart OLS
bash deploy.sh --full   # completo: git pull + build + deploy + restart backend

# Comandos avulsos (usar só se souber o que está fazendo)
sudo systemctl restart cartolafc-backend cartolafc-scheduler
sudo journalctl -u cartolafc-backend -f
```

### Deploy — Como funciona
O OpenLiteSpeed serve o docroot `/www/wwwroot/scoutdados.com.br/` (index.html + assets/ na raiz).
O Vite builda em `frontend/dist/`. O script `deploy.sh` faz a ponte:
1. `bun install` + `bun run build` → gera `frontend/dist/`
2. Copia `dist/index.html` → `./index.html` e `dist/assets/` → `./assets/`
3. Copia estáticos (favicon, og-image, .htaccess, robots.txt)
4. Reinicia OpenLiteSpeed
**Nunca editar `./index.html` ou `./assets/` manualmente** — são sobrescritos a cada deploy.

## Regras de Negócio Cartola

- **Formação:** 12 titulares (1 GOL + 10 linha + 1 TEC), esquemas em `config/settings.py` → `ESQUEMAS_VALIDOS`
- **Capitão:** 1.5x pontos | **Orçamento:** 100 C$ | **Limite:** max 5 jogadores/clube
- **Status IDs (API Cartola):** 7=Provável, 2=Dúvida, 3=Suspenso, 5=Contundido, 6=Nulo
- **Dois times/rodada:** Valorização (C$3-6, maximiza Δpreço) e Pontuação (maximiza score)
- **Scouts:** `config/settings.py` → `SCOUTS` dict (ex: `"G": 8.0`, `"CA": -1.0`)

## Módulos de Análise (`src/analysis/`)

| Módulo | Classe | Uso |
|--------|--------|-----|
| `mpv_calculator.py` | `MPVCalculator` | Mínimo para valorizar: `≈ 0.55 * Preço^1.15` |
| `team_selector.py` | `TeamSelector` | Gera 2 times otimizados, respeita restrições |
| `match_analyzer.py` | `MatchAnalyzer` | Força dos times, prob 1x2, forma recente |
| `confrontos_analyzer.py` | `ConfrontosAnalyzer` | Escalar/evitar times por posição |
| `score_predictor.py` | `ScorePredictor` | V3 híbrido Poisson + frequências contextuais |
| `advanced_predictor.py` | `AdvancedScorePredictor` | h2h + desfalques → `POST /api/previsoes/customizado` |
| `monte_carlo.py` | `MonteCarloSimulator` | Simulação campeonato (título/Liberta/rebaixa) |

## API Cartola Globo

Base: `https://api.cartolafc.globo.com` | Sem auth | Cache 5min | Timeout 15s | Retry 3x (só 5xx)
- `/atletas/mercado` — jogadores + preços (~2MB JSON, campo escudos: `escudos.60x60`)
- `/mercado/status` — mercado aberto/fechado + rodada
- `/atletas/pontuados` — scouts pós-rodada
- `/partidas/{rodada}` — jogos da rodada
- `/clubes` — times (id, nome, escudo)

## Estrutura de Diretórios Chave

```
api_server.py              # TODOS endpoints + Pydantic models + converters (monolítico)
config/settings.py         # Settings (pydantic-settings), posições, scouts, esquemas
src/api/cartola_api.py     # Cliente HTTP síncrono (requests.Session, cache dict interno)
src/analysis/              # 7 módulos de análise (ver tabela acima)
src/database/models.py     # 12 tabelas SQLAlchemy (Clube, Atleta, Partida, Scout, etc.)
src/database/db_manager.py # CRUD com context manager: with self.get_session() as session
src/database/history_manager.py # Escalações + patrimônio (session pattern diferente: manual close)
src/utils/cache.py         # MemoryCache/RedisCache + CircuitBreaker por fonte
src/utils/rate_limiter.py  # slowapi rate limiting
src/scrapers/              # WebScraper (notícias/desfalques)
scheduler_service.py       # 9 jobs APScheduler (5min-6h)

frontend/src/config/api.ts          # API_ENDPOINTS + apiRequest<T> + cartolaApi helper
frontend/src/hooks/useCartolaApi.ts  # 22 hooks React Query (18 queries + 3 mutations + 1 combo)
frontend/src/types/cartola.ts        # Interfaces TS (~625 linhas, espelham Pydantic)
frontend/src/lib/persistor.ts        # localStorage fallback (5 buckets: dashboard, escalacao, etc.)
frontend/src/components/ui/          # 48 componentes shadcn/ui
frontend/src/components/cartola/     # Componentes de domínio (PlayerCard, MatchCard, etc.)
frontend/src/content/posts.ts        # Posts do blog (array de objetos, sem MDX)
frontend/src/pages/Blog.tsx          # Lista de posts
frontend/src/pages/BlogPost.tsx      # Post individual por slug
```

## Gotchas Conhecidos

- **Tudo síncrono:** `CartolaAPI` usa `requests` (bloqueante), endpoints são `def` (não `async def`). `httpx`/`aiohttp` estão nos requirements mas não são usados.
- **POST com query params:** `POST /api/previsoes/customizado` recebe params via `Query()`, não body JSON — o frontend envia como query string.
- **Dois caches separados:** `CartolaAPI._cache` (dict, 5min) vs `src/utils/cache.py` (Memory/Redis). O decorator `@cached` do cache global não é usado nos endpoints.
- **Sem DI:** Instâncias globais singleton, sem dependency injection ou APIRouter.
- **Settings singleton:** `from config.settings import settings` — acesso direto ao objeto global.
- **`strict: false`** no tsconfig do frontend — sem proteção de null checks.
