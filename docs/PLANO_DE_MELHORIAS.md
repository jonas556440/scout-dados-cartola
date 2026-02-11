# Plano de Melhorias — ScoutDados v2

> Data: 2026-02-11 · Branch: `audit-fixes-v2`
> Atualização da v1 — nova Fase 1.5 com quick fixes v2, Fases 2/3 expandidas.

---

## Fase 1: Quick Wins v1 (CONCLUÍDA na audit-fixes)

### Segurança

- [x] **1.1** Remover API key hardcoded de `fixture_collector.py`, mover para `.env`
- [x] **1.2** Restringir `allow_headers` no CORS de `["*"]` para lista específica
- [x] **1.3** Adicionar `request: Request` + `@limiter.limit()` nos endpoints sem rate limit
- [ ] **1.4** Adicionar `_verify_admin_key()` em `/api/historico/salvar` (ver nota)

> **Nota 1.4:** O endpoint é chamado pelo frontend para salvar escalações do usuário. Bloquear com admin key quebraria a funcionalidade. Manter rate limit + validação Pydantic.

### SEO

- [x] **1.5** Trocar `<h1>` da Sidebar para `<span>` — evitar h1 duplo
- [ ] **1.6** Configurar GA4 real (requer Measurement ID do proprietário)
- [x] **1.7** Mover `@import` de fontes para `<link>` + `<link rel="preconnect">`

### Performance

- [x] **1.8** Adicionar `loading="lazy"` em imagens de escudos

---

## Fase 1.5: Quick Wins v2 (ESTA BRANCH — audit-fixes-v2)

### Dados (Urgente)

- [x] **1.9** Corrigir `escudo`→`escudos` em 4 endpoints (`classificacao`, `forca-times`, `times-xg`, `time/{slug}`)
- [x] **1.10** Remover 4 times desatualizados do `TIMES_MAP` (`cuiaba`, `fortaleza`, `juventude`, `sport`)

### Segurança

- [x] **1.11** Restringir CORS `allow_headers` de `["*"]` para headers específicos (reaplicar do audit-fixes v1)
- [x] **1.12** Atualizar `.env.example` — corrigir `APISPORTS_KEY`→`APIFOOTBALL_KEY`, adicionar keys ausentes

### Estabilidade

- [x] **1.13** Adicionar `threading.Lock()` em `_cache_get`/`_cache_set` para thread safety
- [x] **1.14** Corrigir session leak em 3 endpoints de histórico (`try/finally: session.close()`)
- [x] **1.15** Converter `async def` → `def` em `health_check`, `admin_metrics`, `sitemap_xml`

### Performance

- [x] **1.16** Adicionar `manualChunks` no Vite para vendor chunks (Recharts, framer-motion, React Query)

### Limpeza

- [x] **1.17** Mover `score_predictor_v3_backup.py` e `scout-api.service` para `_backup_old_root/`

---

## Fase 2: Médio Prazo (1-2 semanas)

### Consistência de Dados

- [ ] **2.1** Unificar modelo de previsão — usar ScorePredictor V4 (Dixon-Coles) em blog E previsões
- [ ] **2.2** Criar `src/utils/team_mapping.py` — mapeamento central de 20 times (slug, abrev Cartola, ID FDO, nome completo)
- [ ] **2.3** Corrigir mapeamento de siglas FDO→Cartola no `match_page_manager.py`
- [ ] **2.4** Validar match pages antes de indexar — não publicar `enrichment_level: "base"`
- [ ] **2.5** Investigar `jogos: 38` — o fix raiz requer que `match_analyzer.carregar_estatisticas_times()` filtre dados por temporada 2026, não use cumulativos

### Backend

- [ ] **2.6** Converter circuit breaker para sync e aplicar nos endpoints que chamam API Cartola
- [ ] **2.7** Usar context manager (`with history.session_scope() as session:`) nos endpoints SQLAlchemy
- [ ] **2.8** Extrair warm functions para `src/utils/cache_warmup.py` — eliminar import de `api_server` no scheduler
- [ ] **2.9** Calibrar λ do modelo Poisson com resultados reais (`MEDIA_GOLS_MANDANTE` ~1.35, `MEDIA_GOLS_VISITANTE` ~1.05)
- [ ] **2.10** Implementar connection pooling para SQLite (max 5 threads)

### Frontend

- [ ] **2.11** Adicionar skip-to-content no MainLayout (WCAG 2.4.1)
- [ ] **2.12** Consolidar sitemaps — gerar apenas em `dist/`
- [ ] **2.13** Implementar OG images dinâmicas por jogo/time
- [ ] **2.14** Adicionar tratamento de erro granular por endpoint no `useCartolaApi.ts`

---

## Fase 3: Longo Prazo (1-3 meses)

### Arquitetura

- [ ] **3.1** Quebrar `api_server.py` em módulos: `routes/brasileirao.py`, `routes/blog.py`, `routes/historico.py`
- [ ] **3.2** Migrar cache para Redis em produção (atualmente `memory://`)
- [ ] **3.3** Adicionar CI/CD via GitHub Actions (lint + test + deploy)
- [ ] **3.4** Implementar monitoramento (UptimeKuma ou similar)
- [ ] **3.5** Adicionar testes de integração: cache, Monte Carlo, blog_generator

### Produto

- [ ] **3.6** PWA (Service Worker) para uso offline
- [ ] **3.7** Notificações push para escalação parcial/fechamento de mercado
- [ ] **3.8** Dashboard comparativo de modelos (Poisson vs Monte Carlo vs Híbrido)

---

## Priorização Visual

```
Urgência ↑
  │  ┌──────────────────────────────────────┐
  │  │ #21 escudos null  │ #22 siglas FDO   │
  │  │ #24 TIMES_MAP     │ #12 thread safety │  ← Fazer AGORA (Fase 1.5)
  │  ├──────────────────────────────────────┤
  │  │ #2.5 jogos:38     │ #2.6 circuit brk │
  │  │ #2.9 calibrar λ   │ #2.2 team_mapping│  ← Fazer em 1-2 semanas (Fase 2)
  │  ├──────────────────────────────────────┤
  │  │ #3.1 split server │ #3.3 CI/CD       │
  │  │ #3.2 Redis        │ #3.5 testes      │  ← Fazer em 1-3 meses (Fase 3)
  │  └──────────────────────────────────────┘
  └──────────────────────────────── Impacto →
```
