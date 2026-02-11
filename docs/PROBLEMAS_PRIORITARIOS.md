# Problemas Prioritários — ScoutDados v2

> Data: 2026-02-11 · Branch: `audit-fixes-v2`
> Atualização da v1 — adicionados 7 novos achados (#21-#27), revisados os existentes.

---

## Resumo

| Severidade | v1 | v2 (novo) | Total |
|------------|-----|-----------|-------|
| CRÍTICO    | 3   | +2        | **5** |
| ALTO       | 8   | +3        | **11** |
| MÉDIO      | 6   | +2        | **8** |
| BAIXO      | 3   | —         | **3** |
| **Total**  | 20  | **+7**    | **27** |

---

## CRÍTICOS (5)

### 1. 🔴 API Key Hardcoded no Código-Fonte

**Status:** ✅ CORRIGIDO na audit-fixes v1
**Evidência:** `src/analysis/fixture_collector.py` — chave `d354c8d1f1...` removida, agora faz `logger.warning()` se `APIFOOTBALL_KEY` não está configurada.

---

### 2. 🔴 28 de 37 Endpoints Sem Rate Limit Efetivo

**Status:** ✅ CORRIGIDO na audit-fixes v1 (porém não mergeado no main)
**Evidência:** Detectado que no `main` atual os rate limits **não estão aplicados** nos 28 endpoints — as correções estão apenas na branch `audit-fixes`.

**Ação necessária:** Mergear `audit-fixes` ou reaplicar os rate limits nesta branch.

---

### 3. 🔴 POST `/api/historico/salvar` Sem Autenticação

**Status:** ⚠️ Mantido como está — endpoint é usado pelo frontend.
**Mitigação:** Rate limit (200/min default) + validação de payload via Pydantic `SaveTeamRequest`.

---

### 21. 🔴 **NOVO** — `escudo` Singular vs `escudos` Plural (Escudos Null)

**Evidência:** 4 endpoints usam `clube_info.get("escudo")` (singular), mas a API Cartola retorna `escudos` (plural).

| Endpoint | Linha | Status |
|----------|-------|--------|
| `/api/brasileirao/classificacao` | L1718-1719 | ❌ `escudo` singular → `null` |
| `/api/brasileirao/forca-times` | L1493 | ❌ `escudo` singular → `null` |
| `/api/brasileirao/times-xg` | L1558-1560 | ❌ `escudo` singular → `null` |
| `/api/brasileirao/time/{slug}` | L2367-2368 | ❌ `escudo` singular → `null` |

Endpoints que usam corretamente `escudos` (plural): `converter_atleta_para_response` (L277), `converter_partida` (L307), `/api/dashboard` (L874).

**Impacto:** Nenhum escudo aparece nas páginas de Classificação, Força dos Times, xG e Detalhe do Time. O frontend precisa dos escudos para exibir os cards.

**Correção:** Trocar `clube_info.get("escudo")` por `clube_info.get("escudos")` nos 4 endpoints.

---

### 22. 🔴 **NOVO** — Siglas FDO Erradas nas Match Pages

**Evidência:** `data/match_pages/sao-paulo-x-gremio-2026-02-11.json`:
```json
"mandante_sigla": "PAU",   // Deveria ser "SAO"
"visitante_sigla": "FBP",  // Deveria ser "GRE"
```

**Causa:** `match_page_manager.py` L163 propaga `match.get("mandante_sigla")` sem mapeamento FDO→Cartola. A fonte (`fixture_collector.py`) usa IDs do football-data.org que têm siglas diferentes.

**Impacto:** Enriquecimentos (H2H, forma, xG) não são aplicados corretamente pois não encontram os times pelo abreviação correta.

**Correção (Fase 2):** Criar mapeamento central `src/utils/team_mapping.py` com FDO→Cartola.

---

## ALTOS (11)

### 4. 🟠 CORS `allow_headers=["*"]`

**Status:** ✅ CORRIGIDO na audit-fixes v1 (não mergeado no main).
**Ação:** Reaplicar nesta branch — trocar `["*"]` por headers específicos.

---

### 5. 🟠 Circuit Breakers async Não Conectados

**Status:** ❌ Pendente (Fase 2)
**Evidência:** `src/utils/cache.py` L121 — decorators são `async def wrapper(...)`, mas todos endpoints em `api_server.py` são `def` sync. Circuit breakers nunca são ativados.
**Impacto:** Sem circuit breakers, falha na API Cartola causa cascata de timeouts.

---

### 6. 🟠 Previsões Contraditórias (Blog vs Monte Carlo)

**Status:** ❌ Pendente (Fase 2)
**Evidência rodada 3:**
- **Blog:** VIT favorito contra FLA (53.1%)
- **Monte Carlo:** FLA favorito (48.5% → `probVitoriaMandante: 24.0%`)
**Causa:** Modelos diferentes usam dados diferentes (médias Cartola vs stats cumulativas).

---

### 7. 🟠 GA4 com Placeholder — Zero Analytics

**Status:** ❌ Pendente — proprietário ainda não criou a propriedade GA4.
**Evidência:** `frontend/index.html` L49 → `G-XXXXXXXXXX`.
**Ação:** Assim que o proprietário criar o GA4, substituir o placeholder. Adicionado `VITE_GA_ID` ao `.env.example`.

---

### 8. 🟠 `<h1>` Duplicado na Sidebar

**Status:** ✅ CORRIGIDO na audit-fixes v1 — `<h1>` trocado por `<span>` com `role="heading" aria-level={2}`.

---

### 9. 🟠 Fonts Bloqueando Render via `@import`

**Status:** ✅ CORRIGIDO na audit-fixes v1 — movido para `<link>` + `<link rel="preconnect">`.

---

### 10. 🟠 Match Pages com `enrichment_level: "base"` Publicadas

**Status:** ❌ Pendente (Fase 2)
**Evidência:** Match pages marcadas como `"base"` prometem "análise completa" mas não têm dados enriquecidos.

---

### 23. 🟠 **NOVO** — xG Sistematicamente Inflados ~50%

**Evidência do blog rodada 3:** Todos os 10 jogos com xG total entre 3.4-3.9 (vs média real do Brasileirão ~2.3-2.5).
| Jogo | xG Total | xG Esperado |
|------|----------|-------------|
| VAS x BAH | 3.92 | ~2.4 |
| INT x PAL | 3.84 | ~2.4 |
| CAP x SAN | 3.41 | ~2.4 |

**Causa:** O λ base do modelo Poisson (`score_predictor.py`) está calibrado em dados derivados de pontuação Cartola (médias de atletas), não em dados reais de chutes/xG.

**Correção (Fase 2):** Calibrar `MEDIA_GOLS_MANDANTE` e `MEDIA_GOLS_VISITANTE` com resultados reais das primeiras rodadas.

---

### 24. 🟠 **NOVO** — TIMES_MAP Desatualizado (4 times da Série A 2025)

**Evidência:** `src/analysis/blog_generator.py` L690 inclui:
- `cuiaba` → CUI (rebaixado)
- `fortaleza` → FOR (rebaixado)
- `juventude` → JUV (rebaixado)
- `sport` → SPO (rebaixado)

**Impacto:** O scheduler pode tentar gerar blog posts para times que não existem na Série A 2026, causando erros silenciosos ou posts com dados vazios.

**Correção:** Remover os 4 times desatualizados do `TIMES_MAP`.

---

### 25. 🟠 **NOVO** — Scheduler Importa `api_server` Inteiro

**Evidência:** `scheduler_service.py` L1058-1103 faz `from api_server import warm_classificacao_cache, ...` — carrega ~3000 linhas de FastAPI + middlewares + 37 endpoints dentro do processo scheduler.

**Impacto:** Startup lento + ~50MB extra de memória no processo scheduler.

**Correção (Fase 2):** Extrair warm functions para `src/utils/cache_warmup.py`.

---

## MÉDIOS (8)

### 11. 🟡 `.env.example` Inconsistente

**Evidência:** O template usa `APISPORTS_KEY` mas `fixture_collector.py` lê `APIFOOTBALL_KEY`. Também faltam `ADMIN_API_KEY`, `BLOG_API_KEY`, `VITE_GA_ID`.

**Correção:** Atualizar `.env.example` com nomes corretos.

---

### 12. 🟡 Cache in-memory sem Thread Safety

**Evidência:** `api_server.py` L1626 — `_endpoint_caches` é um dict compartilhado sem `threading.Lock()`. Com Uvicorn workers e threads do scheduler, há risco de race condition em `_cache_get`/`_cache_set`.

**Correção:** Adicionar `threading.Lock()` em `_cache_get`/`_cache_set`.

---

### 13. 🟡 Session Leak nos Endpoints de Histórico

**Evidência:** 3 endpoints (`/api/historico/rodadas`, `/rodada/{rodada}`, `/status`) fazem `session.close()` apenas no happy path. Qualquer exceção causa session leak.

**Correção:** Envolver em `try/finally: session.close()`.

---

### 14. 🟡 `escudos/escudo` Inconsistência

**Status:** Subsumido pelo item #21 (mesmo bug).

---

### 15. 🟡 TIMES_MAP Duplicado em 4+ Módulos

**Evidência:** `blog_generator.py`, `match_page_manager.py`, `fixture_collector.py`, `web_scraper.py` — todos definem mapeamentos de times separadamente.

**Correção (Fase 2):** Centralizar em `src/utils/team_mapping.py`.

---

### 16. 🟡 Logrotate com Path Errado

**Evidência:** `hardening_security.sh` configura logrotate para `/var/log/cartolafc/` mas os services escrevem em `./logs/`.

---

### 26. 🟡 **NOVO** — `async def` em 3 Endpoints

**Evidência:** `health_check` (L2786), `admin_metrics` (L2797), `sitemap_xml` (L2808) usam `async def` quando a convenção do projeto é `def` sync.

**Nota:** Estes 3 são leves (sem I/O bloqueante), então o impacto é mínimo. Converter para manter consistência.

---

### 27. 🟡 **NOVO** — Vite sem `manualChunks`

**Evidência:** `frontend/vite.config.ts` não tem configuração de `build.rollupOptions.output.manualChunks`. Recharts (~200KB), framer-motion (~100KB), and React Query ficam no bundle principal.

**Correção:** Adicionar chunk splitting em `vite.config.ts`.

---

## BAIXOS (3)

### 17. 🔵 Sem skip-to-content (WCAG 2.4.1)

Nenhum link skip-to-content encontrado no `MainLayout`.

---

### 18. 🔵 `scout-api.service` Obsoleto

Arquivo existe na raiz mas não é usado. Aponta para `/root/cartolafc2026` (path antigo).

---

### 19. 🔵 Testes Insuficientes

Apenas 2 arquivos de teste: `test_api_smoke.py` (150 linhas) e `test_security.py` (93 linhas). Sem testes de integração, cache, Monte Carlo, blog_generator.

---

### 20. 🔵 `score_predictor_v3_backup.py` Órfão

Arquivo de backup (793 linhas) sem uso. O preditor atual é `score_predictor.py` (V4).
