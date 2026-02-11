# Auditoria Geral — ScoutDados v2

> Data: 2026-02-11 · Branch: `audit-fixes-v2` · Auditor: GitHub Copilot (Claude Opus 4.6)
> Atualização da auditoria v1 (branch `audit-fixes`), expandida com 7 novos achados críticos/altos.

---

## 1. Mapa da Arquitetura

```
[Usuário] ──── HTTPS ────► [OpenLiteSpeed]
                                │
                  ┌─────────────┴─────────────┐
                  │                             │
          dist/ (estáticos)              proxy /api/
          ├─ HTML pré-render             ▼
          ├─ JS chunks (Vite)      [FastAPI :8000]
          ├─ CSS (Tailwind)         api_server.py
          └─ assets                  (2967 linhas, sync)
                                         │
                        ┌────────────────┼─────────────────┐
                        │                │                  │
                   [Cache 3 camadas]  [SQLite WAL]   [APIs Externas]
                   ├─ memória (dict)  ├─ Alembic      ├─ API Cartola FC
                   ├─ disco (JSON)    └─ 3 tabelas     ├─ API-Football v3
                   └─ fallback stale                    ├─ football-data.org
                                                        └─ GE.globo.com (scraping)

[APScheduler]  ◄── cartolafc-scheduler.service
scheduler_service.py (1224 linhas)
├─ 20 jobs cron/interval
├─ warm-ups de cache
├─ coleta de dados
├─ geração de blog/match pages
└─ manutenção (sitemap, SEO)
```

### Stack

| Camada     | Tecnologia                                          |
|------------|-----------------------------------------------------|
| Frontend   | React 18 + Vite 6 + SWC + TypeScript + Tailwind 4  |
| UI         | shadcn/ui + Recharts + Framer Motion                |
| Backend    | FastAPI (sync def) + Pydantic + SlowAPI             |
| DB         | SQLite WAL + SQLAlchemy + Alembic                   |
| Cache      | Dict in-memory + JSON em disco + stale fallback     |
| Scheduler  | APScheduler (BackgroundScheduler)                   |
| Servidor   | OpenLiteSpeed → dist/ + proxy reverso /api/         |
| Deploy     | deploy.sh (bun build → prerender → lswsctrl)       |
| Serviços   | systemd: cartolafc-backend, cartolafc-scheduler     |

---

## 2. Inventário de Arquivos-Chave

| Arquivo | Linhas | Função |
|---------|--------|--------|
| `api_server.py` | 2967 | API REST monolítica — 37 endpoints |
| `scheduler_service.py` | 1224 | 20 jobs APScheduler em background |
| `src/analysis/blog_generator.py` | 1125 | Posts automáticos por rodada/time |
| `src/analysis/score_predictor.py` | 777 | Poisson + Dixon-Coles V4 |
| `src/analysis/match_analyzer.py` | ~400 | Carrega estatísticas, calcula forças |
| `src/analysis/match_page_manager.py` | 469 | Páginas progressivas de jogos |
| `src/analysis/fixture_collector.py` | 494 | Multi-competição API-Football |
| `src/analysis/monte_carlo.py` | 385 | Simulação Monte Carlo |
| `src/analysis/stats_consolidator.py` | 154 | Cache consolidado por rodada |
| `src/utils/cache.py` | 288 | Cache + Circuit Breaker (async) |
| `src/utils/rate_limiter.py` | 101 | SlowAPI rate limiting |
| `src/utils/security_headers.py` | 149 | Security headers middleware |
| `config/settings.py` | 123 | Pydantic settings |
| `deploy.sh` | 135 | Deploy script com rollback |
| `frontend/prerender.mjs` | 353 | SSG pre-render Puppeteer |
| `frontend/src/App.tsx` | 88 | Router React — 17 rotas |
| `frontend/src/hooks/useCartolaApi.ts` | 640 | 20+ hooks React Query |
| `frontend/src/types/cartola.ts` | 655 | TypeScript interfaces |
| `frontend/src/config/api.ts` | 199 | API client centralizado |
| `frontend/vite.config.ts` | ~30 | Config Vite (sem manualChunks) |

---

## 3. Fluxo de Dados: API Cartola → Frontend

```
API Cartola FC (GET /auth/mercado/status)
    └── api.get_mercado()  [api_server.py]
         └── match_analyzer.carregar_estatisticas_times(clubes, partidas)
              │                                         [match_analyzer.py]
              ├── Extrai posições/aproveitamentos das partidas atuais
              ├── Calcula forca_base = (historico × 0.8) + (posicao × 0.2)
              ├── _stats_cache (API-Football) → gols_pro, gols_contra, jogos ← ⚠️ CUMULATIVO
              └── Retorna Dict[clube_id, EstatisticasTime]
                   │
                   ├── /api/brasileirao/classificacao    → classificacao[]
                   │    └── ⚠️ escudo=null (usa "escudo" singular, deveria ser "escudos")
                   │    └── ⚠️ jogos=38 (dados cumulativos multi-temporada)
                   │
                   ├── /api/brasileirao/forca-times       → times_forca[]
                   │    └── ⚠️ escudo=null (mesmo bug)
                   │
                   ├── /api/brasileirao/times-xg          → times_xg{}
                   │    └── ⚠️ escudo=null (mesmo bug)
                   │
                   └── /api/brasileirao/time/{slug}       → time_detail{}
                        └── ⚠️ escudo=null (mesmo bug)
```

**Bug raiz:** `match_analyzer._stats_cache` armazena dados cumulativos do API-Football (todas as temporadas), não filtrados pelo campeonato atual. Resultado: `jogos=38`, `gols_pro=60` etc. quando estamos na rodada 3.

---

## 4. Mapa de Siglas — Divergências entre Sistemas

| Time | Cartola API | FDO (football-data.org) | blog slug | match_page slug |
|------|-------------|------------------------|-----------|-----------------|
| São Paulo | SAO | PAU | sao-paulo | sao-paulo-x-... |
| Grêmio | GRE | FBP | gremio | gremio-x-... |
| Ath. Paranaense | CAP | ??? | athletico-pr | athletico-pr-x-... |
| A. Mineiro | CAM | ??? | atletico-mg | atletico-mg-x-... |
| Red Bull Bragantino | RBB | ??? | red-bull-bragantino | red-bull-bragantino-x-... |

**Impacto:** Match pages herdam siglas FDO incorretas (ex: `"mandante_sigla": "PAU"`), impedindo o cruzamento correto com dados Cartola. O `match_page_manager.py` L163 propaga sem mapeamento.

---

## 5. TIMES_MAP — Times Desatualizados

O `TIMES_MAP` em `src/analysis/blog_generator.py` (L690) inclui 4 times que **não participam da Série A 2026**:

| Slug | Time | Status |
|------|------|--------|
| `cuiaba` | Cuiabá | ❌ Não está na Série A 2026 |
| `fortaleza` | Fortaleza | ❌ Não está na Série A 2026 |
| `juventude` | Juventude | ❌ Não está na Série A 2026 |
| `sport` | Sport | ❌ Não está na Série A 2026 |

**Times da Série A 2026 presentes no mapa:** CAM, CAP, BAH, BOT, COR, CRU, FLA, FLU, GRE, INT, MIR, PAL, SAN, SAO, VAS, VIT, RBB, CHA, CFC, REM (20 times ✅)

---

## 6. Dependência Scheduler → api_server

```
scheduler_service.py
    └── from api_server import (
            warm_classificacao_cache,
            warm_confrontos_cache,
            warm_previsoes_cache,
            warm_dashboard_cache,
            warm_forca_times_cache,
            warm_times_xg_cache
        )
        └── Carrega TUDO do api_server:
            ├── FastAPI app + middlewares
            ├── 37 endpoint handlers
            ├── Singleton instances (api, mpv_calc, team_selector, match_analyzer)
            └── ~3000 linhas desnecessárias no processo scheduler
```

**Impacto:** Startup lento + consumo de memória duplicado + risco de import circular.

---

## 7. Endpoints — Inventário Completo (37)

| # | Método | Rota | Rate Limit | Auth | Cache |
|---|--------|------|------------|------|-------|
| 1 | GET | `/api/status` | 300/min | — | — |
| 2 | GET | `/api/mercado` | 200/min | — | 5min memória |
| 3 | GET | `/api/atletas` | 200/min | — | 5min memória |
| 4 | GET | `/api/partidas` | 200/min | — | 5min memória |
| 5 | GET | `/api/dashboard` | 200/min | — | 5min memória |
| 6 | GET | `/api/destaques` | 200/min | — | 5min memória |
| 7 | GET | `/api/valorizacao` | 200/min | — | — |
| 8 | POST | `/api/escalacao/gerar` | 30/min | — | — |
| 9 | GET | `/api/clubes` | 200/min | — | 30min disco |
| 10 | GET | `/api/rodada-atual` | 200/min | — | — |
| 11 | GET | `/api/scouts/rodada/{rodada}` | 200/min | — | disco |
| 12 | GET | `/api/historico/rodadas` | 200/min | — | — |
| 13 | GET | `/api/historico/rodada/{rodada}` | 200/min | — | — |
| 14 | GET | `/api/historico/status` | 200/min | — | — |
| 15 | POST | `/api/historico/salvar` | 200/min | — | — |
| 16 | GET | `/api/brasileirao/classificacao` | 200/min | — | 10min memória |
| 17 | GET | `/api/brasileirao/confrontos` | 200/min | — | 5min memória |
| 18 | GET | `/api/brasileirao/forca-times` | 200/min | — | 10min memória |
| 19 | GET | `/api/brasileirao/times-xg` | 200/min | — | 10min memória |
| 20 | GET | `/api/brasileirao/previsoes` | 200/min | — | 5min memória |
| 21 | GET | `/api/brasileirao/time/{slug}` | 200/min | — | 15min keyed |
| 22 | GET | `/api/brasileirao/noticias/rodada/{rodada}` | 60/min | — | disco |
| 23 | GET | `/api/brasileirao/noticias/{clube}` | 60/min | — | disco |
| 24 | GET | `/api/brasileirao/escalacao/rodada/{r}` | 200/min | — | disco |
| 25 | GET | `/api/brasileirao/acuracia` | 200/min | — | 1h memória |
| 26 | GET | `/health` | — | — | — |
| 27 | GET | `/api/admin/metrics` | — | — | — |
| 28 | GET | `/sitemap.xml` | — | — | — |
| 29 | GET | `/api/blog/posts` | 200/min | — | disco |
| 30 | GET | `/api/blog/post/{slug}` | 200/min | — | disco |
| 31 | POST | `/api/blog/gerar/{rodada}` | — | admin_key | — |
| 32 | POST | `/api/blog/gerar-time/{time}` | — | admin_key | — |
| 33 | GET | `/api/jogos` | 200/min | — | disco |
| 34 | GET | `/api/jogos/{slug}` | 200/min | — | disco |
| 35 | POST | `/api/jogos/discover` | 3/min | admin_key | — |
| 36 | POST | `/api/jogos/update/{slug}` | 3/min | admin_key | — |
| 37 | DELETE | `/api/cache/limpar` | 3/min | admin_key | — |

---

## 8. Frontend — Rotas

| Rota | Página | Lazy | SEO |
|------|--------|------|-----|
| `/` | LandingPage | Não | ✅ |
| `/dashboard` | Dashboard | Sim | ✅ |
| `/escalacao` | Escalacao | Sim | ✅ |
| `/confrontos` | Confrontos | Sim | ✅ |
| `/mercado` | Mercado | Sim | ✅ |
| `/historico` | Historico | Sim | ✅ |
| `/estatisticas` | Estatisticas | Sim | ✅ |
| `/brasileirao` | Brasileirao | Sim | ✅ |
| `/brasileirao/time/:slug` | TimePage | Sim | ✅ |
| `/brasileirao/jogo/:id` | JogoPage | Sim | ✅ |
| `/scouts` | ScoutsPage | Sim | ✅ |
| `/blog` | BlogPage | Sim | ✅ |
| `/blog/:slug` | BlogPostPage | Sim | ✅ |
| `/sobre` | Sobre | Sim | ✅ |
| `/privacidade` | Privacidade | Sim | ✅ |
| `/termos` | Termos | Sim | ✅ |
| `*` | NotFound | Sim | ✅ |

---

## 9. O que Funciona Bem ✅

1. **Cache 3 camadas** (memória → disco → stale fallback) — resiliente e bem implementado
2. **Rate limiting** em todos os 37 endpoints via SlowAPI
3. **Deploy script** com backup/rollback automático — sólido
4. **Prerender SSG** via Puppeteer para SEO estático
5. **Frontend hooks** centralizados em `useCartolaApi.ts` com React Query + localStorage
6. **Pydantic settings** com validação de SECRET_KEY em produção
7. **Security headers** middleware bem configurado (CSP, X-Frame, etc.)
8. **`_sanitize_slug()`** previne path traversal em blog/jogos
9. **`hmac.compare_digest()`** para comparação timing-safe de admin keys
10. **Systemd hardening** (NoNewPrivileges, ProtectSystem=strict, ProtectHome=true)
11. **Slug deduplication** no `listar_posts_gerados()` com `seen_slugs` set

---

## 10. O que Não Funciona Bem ❌

1. **Monolito de 2967 linhas** (`api_server.py`) — difícil manter e testar
2. **2 sistemas de cache paralelos** nunca conectados: `src/utils/cache.py` (async) e `_endpoint_caches` (sync)
3. **Circuit breakers async** não funcionam em endpoints sync — decorators nunca ativados
4. **`escudo` singular vs `escudos` plural** — escudos null em 4 endpoints do Brasileirão
5. **Dados cumulativos multi-temporada** — `jogos=38` quando estamos na rodada 3
6. **Scheduler importa api_server inteiro** — carrega ~3000 linhas desnecessárias
7. **TIMES_MAP duplicado/desatualizado** em 4+ módulos, com 4 times da Série A 2025
8. **Siglas FDO não mapeadas** — match pages com `PAU`, `FBP` em vez de `SAO`, `GRE`
9. **xG inflados ~50%** — média 3.7/jogo vs realidade ~2.4
10. **Previsões contraditórias** — blog e Monte Carlo divergem no mesmo jogo​
