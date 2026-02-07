# ScoutDados.com.br — Implementação Completa: Portal de Estatísticas de Futebol

> **Domínio:** scoutdados.com.br (já registrado e operacional)  
> **Stack:** FastAPI + React + Vite + Tailwind + Recharts  
> **Data:** Fevereiro 2026  
> **Status atual:** 100% Cartola FC → Expandindo para Estatísticas Gerais do Brasileirão

---

## 1. VISÃO GERAL DA EXPANSÃO

### 1.1 Estado Atual vs Futuro

| Aspecto | Hoje | Depois |
|---------|------|--------|
| **Foco** | Apenas Cartola FC | Cartola FC + Brasileirão + Scouts |
| **Páginas** | 10 | 16+ (+ Brasileirão, Scouts, Simulador, Blog, Privacidade, Termos) |
| **Endpoints** | 17 | 25+ |
| **Fontes de dados** | API Cartola (1 fonte) | 4+ fontes com fallback (sem odds/apostas) |
| **SEO** | SPA sem SSR, meta tags estáticas | Meta tags dinâmicas, sitemap, blog indexável |
| **Monetização** | Nenhuma | AdSense (fantasy + estatísticas = permitido) |

### 1.2 Arquitetura Expandida

\`\`\`
scoutdados.com.br/
├── / (Landing Page — hub central)
├── /brasileirao (NOVO — pilar de estatísticas)
│   ├── Classificação + Probabilidades (tipo chancedegol.com.br)
│   ├── Previsão de placares por rodada (top 5 placares, faixas de gols, ambos marcam)
│   ├── Ranking de força dos times
│   ├── Resultados vs Previsões (acurácia do modelo)
│   └── Simulador de jogos customizados
├── /cartola (EXISTENTE — ferramentas Cartola)
│   ├── /dashboard, /escalacao, /mercado, /confrontos, /historico, /estatisticas
├── /scouts (NOVO — análise individual de jogadores)
│   ├── Destaques da rodada (top pontuadores)
│   ├── Decepções (expectativa vs realidade)
│   ├── Desfalques confirmados
│   └── Busca por jogador (histórico completo)
├── /blog (NOVO — conteúdo SEO)
├── /privacidade (NOVO — obrigatório AdSense)
├── /termos (NOVO — obrigatório AdSense)
└── /sobre (EXISTENTE — atualizar identidade)
\`\`\`

### 1.3 Navegação Proposta

\`\`\`
ScoutDados
├── 🏆 Brasileirão
│   ├── Classificação & Probabilidades
│   ├── Previsão de Placares
│   └── Simulador de Jogos
├── ⚽ Cartola FC
│   ├── Dashboard, Escalação, Mercado, Confrontos, Histórico
├── 📊 Scouts & Análises
│   ├── Destaques da Rodada
│   ├── Desfalques
│   └── Estatísticas
├── 📰 Blog
└── ℹ️ Sobre
\`\`\`

---

## 2. FONTES DE DADOS — COMPLETAS COM FALLBACK

### 2.1 Hierarquia de Fontes (Prioridade)

> **Regra de ouro:** Nenhuma fonte de odds/apostas no MVP. Probabilidades são 100% calculadas internamente (Poisson + Monte Carlo). Isso mantém o site na zona segura de "estatística/simulação" para AdSense.

| # | Fonte | Dados | Custo | Limite | Fallback |
|---|-------|-------|-------|--------|----------|
| 1 | **API Cartola FC Globo** | Atletas, preços, scouts, partidas | Grátis | Sem limite (cache 5min) | — |
| 2 | **football-data.org** | Partidas, classificação, times, artilheiros | Grátis | 10 req/min (throttle) | API Cartola (calcular) |
| 3 | **Dataset histórico (CSV local)** | Resultados 2003-2024 (+APIs para atual) | Grátis | Ilimitado (local) | football-data.org |
| 4 | **FBref (scraping)** | xG, xA, passes, tackles/90min | Grátis | ~20 req/min | Scouts Cartola |
| 5 | **API-Football (RapidAPI)** | Resultados, estatísticas | Grátis | 100 req/dia | Demais fontes |
| 6 | **GE.globo.com (scraping)** | Desfalques, escalações | Grátis | Rate-limited | Status Cartola |

### 2.2 Detalhes de Cada Fonte

#### 2.2.1 API Cartola FC Globo (JÁ INTEGRADA)

- **Base URL:** https://api.cartolafc.globo.com
- **Autenticação:** Nenhuma
- **Endpoints:** /atletas/mercado, /mercado/status, /atletas/pontuados, /partidas/{rodada}, /clubes, /rodadas
- **Cache:** 5 minutos | **Retry:** 3x com 1s delay
- **Classificação:** Extrair de /partidas/{rodada} iterando rodadas 1-N (serve para temporada atual; depende da disponibilidade dos endpoints do Cartola)

#### 2.2.2 football-data.org (INTEGRAR — MELHOR OPÇÃO GRATUITA)

- **Base URL:** https://api.football-data.org/v4
- **Free Tier:** 10 req/min, 12 ligas incluindo Série A Brasil (BSA)
- **Endpoints:** /competitions/BSA/standings, /competitions/BSA/matches, /competitions/BSA/teams, /competitions/BSA/scorers
- **Auth:** Header `X-Auth-Token` (obrigatório em toda request)
- **Registro:** https://www.football-data.org/client/register

**⚠️ CORE — Cache + Backoff + Fallback são obrigatórios, não opcionais:**

```python
# Configuração MÍNIMA para football-data.org
FOOTBALL_DATA_CONFIG = {
    "cache_ttl": 600,           # 10 min (respeitando 10 req/min)
    "backoff_base": 2,          # 2s, 4s, 8s (exponencial)
    "max_retries": 3,
    "timeout": 15,
    "rate_limit_per_min": 10,   # free tier — NÃO ultrapassar
    "fallback_ordem": ["api_cartola_calc", "dataset_local", "api_football"],
}
```

- **Se receber 429 (Rate Limit):** backoff exponencial, NÃO retry imediato
- **Se API fora do ar:** fallback automático para API Cartola (calcular classificação) ou dataset local
- **Cron recomendado:** 1 chamada de standings a cada 30min (via scheduler), resultado em cache SQLite

#### 2.2.3 Dataset Histórico (CSV Local)

- **Origem:** Datasets públicos de Brasileirão (ex: adaoduque/Brasileirao_Dataset no GitHub, repo público atualizado pelo autor)
- **Formato:** CSV com resultados completos (2003-2024): data, mandante, visitante, gols, público, árbitro, cartões, gols por jogador
- **⚠️ Importante:** Dataset público vai até 2024. Temporada 2025/2026 deve ser completada via football-data.org ou API Cartola
- **Estratégia:** Não hardcode anos no código; detectar último ano disponível no CSV e usar APIs para complementar temporada atual
- **Uso:** Download único → importação para SQLite/Postgres → base de h2h (histórico de confrontos), médias de gols casa/fora, tendências por estádio
- **Atualização:** Manual ou via script a cada temporada (dados históricos não mudam)
- **Vantagem:** Zero dependência de API externa para dados passados — funciona 100% offline

#### 2.2.4 ~~The Odds API~~ — REMOVIDO DO MVP

> **Decisão:** Odds de casas de apostas ficam **FORA do v1.0**. Mesmo como "referência estatística", integrar odds puxa o site para zona cinza de "aposta" e aumenta risco de classificação indevida pelo AdSense/Google. Todas as probabilidades (1x2, faixas de gols, ambos marcam) são calculadas internamente pelo ScorePredictor V3 (Poisson + frequências contextuais).
>
> **Futuro (v2.0+):** Se houver demanda comprovada e o AdSense já estiver aprovado e estável, avaliar integração com linguagem 100% estatística ("probabilidade implícita do mercado" vs "probabilidade do modelo").

#### 2.2.5 FBref (Scraping com cautela)

- **URL Série A:** https://fbref.com/en/comps/24/Serie-A-Stats
- **Dados:** xG, xGA, progressive passes, shot-creating actions, per 90 stats
- **Rate:** ~20 req/min | **Recomendação:** 1x/dia via cron → cache SQLite
- **Alt:** pip install soccerdata → sd.FBref("BRA-Serie A", "2026")
- **Risco:** FBref pode bloquear scraping a qualquer momento → fallback = Scouts Cartola

#### 2.2.6 API-Football (BACKUP EMERGENCIAL)

- **Via RapidAPI:** api-football-v1.p.rapidapi.com/v3
- **Free:** 100 req/dia (MUITO limitado — usar SOMENTE como último fallback)
- **Registro:** https://rapidapi.com/api-sports/api/api-football
- **Estratégia:** NÃO usar como fonte primária. Apenas quando football-data.org + dataset local + FBref todos falharem

### 2.3 Sistema de Fallback (Pseudocódigo)

\`\`\`python
import asyncio
from datetime import datetime, timedelta

class DataAggregator:
    """Agregador multi-fonte com cache, backoff exponencial e fallback."""
    
    FONTES_CLASSIFICACAO = [
        ("football_data_org", 600),    # cache 10 min
        ("dataset_local",     86400),  # cache 24h (dados estáticos)
        ("api_cartola_calc",  1800),   # cache 30 min (calcular dos resultados)
        ("api_football",      3600),   # cache 1h (último recurso)
    ]
    
    def __init__(self):
        self._cache = {}        # {chave: (dados, expira_em)}
        self._backoff = {}      # {fonte: próximo_retry_permitido}
    
    async def obter_classificacao(self) -> dict:
        for fonte, cache_seg in self.FONTES_CLASSIFICACAO:
            # Respeitar backoff
            if fonte in self._backoff and datetime.now() < self._backoff[fonte]:
                continue
            try:
                dados = await self._buscar_com_cache(fonte, cache_seg)
                if dados:
                    self._backoff.pop(fonte, None)  # limpar backoff se OK
                    return dados
            except RateLimitError:
                # Backoff exponencial: 2s → 4s → 8s → 16s → 32s
                tentativas = self._backoff.get(f"{fonte}_count", 0) + 1
                delay = min(2 ** tentativas, 60)
                self._backoff[fonte] = datetime.now() + timedelta(seconds=delay)
                self._backoff[f"{fonte}_count"] = tentativas
                logger.warning(f"{fonte}: rate limited, backoff {delay}s")
            except Exception as e:
                logger.warning(f"{fonte} falhou: {e}")
        
        raise AllSourcesFailedError("Todas as fontes falharam")
\`\`\`

---

## 3. PÁGINA BRASILEIRÃO — DETALHADA

### 3.1 Seções da Página

1. **Classificação com Probabilidades** (tabela principal tipo Chance de Gol)
2. **Previsão de Placares da Rodada** (próximos jogos com top 5 placares)
3. **Resultados vs Previsões** (acurácia do modelo)
4. **Ranking de Força dos Times** (gráfico + tabela)
5. **Probabilidades por Pontuação** (pontos necessários para cada objetivo)

### 3.2 Classificação com Probabilidades

| Pos | Time | Pts | J | V | E | D | GP | GC | SG | Prob Título | Prob Liberta | Prob Sula | Prob Rebaixa |
|-----|------|-----|---|---|---|---|----|----|----| ------------|-------------|-----------|-------------|
| 1 | Botafogo | 3 | 1 | 1 | 0 | 0 | 4 | 0 | 4 | 18.2% | 84.2% | 14.9% | 0.06% |

**Cálculo via Monte Carlo (5.000-10.000 simulações)** usando ScorePredictor V3 existente.
- **10.000 simulações:** maior precisão, ~8-12s de processamento
- **5.000 simulações:** precisão suficiente (~0.5% diferença), ~4-6s
- **Estratégia:** 10k para cron background (cache 1h), 5k para requests on-demand
- **Otimização:** Paralelizar simulações com `asyncio.gather()` ou `multiprocessing`

### 3.3 Previsão de Placares por Jogo

Cada card mostra:
- Mandante vs Visitante (escudos)
- Placar provável + probabilidade
- xG de cada time
- Top 5 placares mais prováveis (%)
- Probabilidades: Vitória casa / Empate / Vitória fora
- Probabilidade de faixas de gols: 0–1, 2–3, 4+ gols (%)
- Ambos marcam (%)
- Confiança do modelo (0-100%)

### 3.4 Resultados vs Previsões

Comparação pós-rodada com métricas acumuladas:
- Acerto exato do placar: X%
- Acerto do resultado (1x2): X%
- Acerto da tendência: X%
- Erro médio de xG: ±X.XX

### 3.5 Probabilidades por Pontuação

| Probabilidade | Título | Libertadores | Sul-Americana | Permanência |
|---------------|--------|--------------|---------------|-------------|
| 100% | 112 | 97 | 78 | 66 |
| 99% | 87 | 65 | 53 | 46 |
| 95% | 82 | 64 | 52 | 45 |
| 90% | 81 | 63 | 51 | 44 |

---

## 4. PÁGINA SCOUTS — DETALHADA

### 4.1 Destaques da Rodada (Top 10)

| Pos | Jogador | Time | Pos | Pontos | G | A | SG | Preço | Variação |
|-----|---------|------|-----|--------|---|---|----|----|----------|
| 1 | Gabriel Menino | PAL | MEI | 18.5 | 1 | 1 | ✅ | C\$6.50 | +C\$1.20 |

### 4.2 Decepções (Top 5 custo-benefício ruim)

Jogadores >C\$10 que pontuaram abaixo da média.

### 4.3 Desfalques Confirmados

Dados do WebScraper existente (/api/noticias/rodada/{rodada}).
Status: 🔴 Lesionado | 🟡 Dúvida | 🔴 Suspenso | 🟠 Poupado

### 4.4 Busca por Jogador

- Input com autocomplete
- Gráfico pontuação por rodada (LineChart)
- Tendência de preço (AreaChart)
- Scouts detalhados (tabela)
- Confrontos futuros com dificuldade

---

## 5. SIMULADOR DE JOGOS

Interface com 2 selects (times) + 2 sliders (força 0-100) + botão simular.
Backend: JÁ IMPLEMENTADO em POST /api/previsoes/customizado (api_server.py L1292).
Usa AdvancedScorePredictor com h2h + desfalques.

---

## 6. NOVOS ENDPOINTS BACKEND

### 6.1 A Criar

\`\`\`python
GET  /api/brasileirao/classificacao     # Classificação + probabilidades Monte Carlo
GET  /api/brasileirao/rodada/{rodada}   # Resultados + comparação previsão vs real
GET  /api/brasileirao/acuracia          # Métricas acumuladas do modelo
GET  /api/scouts/destaques              # Top pontuadores + decepções
GET  /api/scouts/jogador/{atleta_id}    # Histórico completo de um jogador
GET  /api/scouts/desfalques             # Desfalques consolidados
GET  /sitemap.xml                       # Sitemap dinâmico
\`\`\`

### 6.2 Existentes — Conectar ao Frontend

\`\`\`python
GET  /api/previsoes/placares         # L517 — NÃO mapeado no frontend
POST /api/previsoes/customizado      # L1292 — NÃO mapeado
GET  /api/noticias/{clube_abrev}     # L1203 — NÃO mapeado
GET  /api/noticias/rodada/{rodada}   # L1230 — NÃO mapeado
GET  /api/times/forca                # L1360 — NÃO mapeado
GET  /api/confrontos/analise         # L605 — Hook EXISTE mas NUNCA USADO
\`\`\`

---

## 7. NOVOS ARQUIVOS

### 7.1 Backend (Python)

\`\`\`
src/scrapers/football_data_collector.py   # Coletor multi-fonte com fallback
src/analysis/monte_carlo.py               # Simulação probabilities campeonato
src/database/models.py                    # Tabelas: previsoes, resultados, acuracia
\`\`\`

### 7.2 Frontend (TypeScript/React)

\`\`\`
frontend/src/pages/Brasileirao.tsx        # Classificação + previsões + simulador
frontend/src/pages/Scouts.tsx             # Destaques + desfalques + busca
frontend/src/pages/Privacidade.tsx        # Política de privacidade
frontend/src/pages/Termos.tsx             # Termos de uso
frontend/src/content/posts/*.mdx          # Posts do blog
\`\`\`

### 7.3 Tipos TypeScript (adicionar em cartola.ts)

ClassificacaoTime, ClassificacaoResponse, ResultadoRodada, RodadaResponse,
TopPlacar, PrevisaoJogo, PrevisaoRodadaResponse, DestaqueRodada,
DecepcaoRodada, DestaquesResponse, Desfalque, DesfalquesResponse

### 7.4 Hooks React Query (adicionar em useCartolaApi.ts)

useClassificacao, useRodadaBrasileirao, useAcuraciaModelo,
usePrevisaoPlacares, usePrevisaoCustomizada (mutation),
useDestaques, useDesfalques, useHistoricoJogador, useNoticiasRodada

---

## 8. SEO & ADSENSE

### 8.1 Requisitos AdSense

| Requisito | Status | Ação |
|-----------|--------|------|
| 30+ páginas | ❌ | Blog + institucionais |
| Política Privacidade | ❌ | Criar /privacidade |
| Termos de Uso | ❌ | Criar /termos |
| Google Analytics | ❌ | Ativar (ID comentado) |
| Search Console | ❌ | Verificar + sitemap |
| Sitemap XML | ❌ | Endpoint dinâmico |
| Meta tags dinâmicas | ❌ | react-helmet-async |
| Conteúdo original | ✅ | Algoritmos próprios |
| Sem aposta | ✅ | Fantasy = seguro |

### 8.2 O Que PODE vs NÃO PODE (AdSense)

| ✅ PERMITIDO | ❌ PROIBIDO |
|-------------|------------|
| Probabilidades 1x2 | Links casas de apostas |
| Previsão placares | "Aposte aqui" |
| Fantasy (Cartola) | Odds como "dica de aposta" |
| Simulador | Promoção de gambling |
| xG, +2.5 gols, Ambos marcam | Links afiliados de bets |
| Linguagem: "projeção", "simulação" | Linguagem: "palpite certo", "lucro" |

> **✅ Já aplicado:** Frontend rebranded — linguagem 100% estatística: "faixas de gols", "ambos marcam", sem termos de betting (MatchCard.tsx, Confrontos.tsx)

---

## 9. CRONOGRAMA (PRIORIZADO)

### 9.1 Ordem Sugerida (Impacto vs Esforço)

| Fase | Descrição | Tempo | Prioridade |
|------|-----------|-------|------------|
| **1** | **Conectar endpoints órfãos** (/previsoes/placares, /noticias/rodada, /times/forca) | 2-3 dias | 🔴 ALTA (baixo esforço, alto impacto) |
| **5** | **SEO & AdSense obrigatório** (privacidade, termos, sitemap, analytics, robots.txt) | 3-4 dias | 🔴 CRÍTICO (requisito AdSense) |
| **2** | **Página Brasileirão** (classificação + Monte Carlo + previsões) | 5-7 dias | 🟡 MÉDIA (diferencial competitivo) |
| **3** | **Página Scouts** (destaques + desfalques + busca) | 3-4 dias | 🟡 MÉDIA |
| **4** | **Simulador de jogos** (frontend + conectar endpoint) | 2 dias | 🟢 BAIXA (já tem backend) |
| **6** | **Blog MDX** + posts iniciais (pode ser incremental) | 3-4 dias | 🟢 BAIXA (SEO long-term) |
| **7** | **Monitoramento** (Sentry, UptimeRobot, logs estruturados) | 1-2 dias | 🟡 MÉDIA |
| **8** | **Cache Redis + Circuit Breaker** | 1-2 dias | 🔴 ALTA (estabilidade) |
| **TOTAL** | | **21-30 dias** | |

### 9.2 MVP Mínimo (Se Tempo Limitado)

**Fazer nesta ordem para lançar rápido:**
1. Fase 1 (endpoints órfãos) — 2 dias
2. Fase 5 (AdSense obrigatório) — 3 dias
3. Fase 8 (Cache Redis) — 1 dia
4. **LANÇAR v0.9** com Cartola + estrutura AdSense
5. Fase 2 (Brasileirão) — 5 dias
6. **LANÇAR v1.0** completo

---

## 10. VARIÁVEIS DE AMBIENTE

\`\`\`bash
# APIs Externas
FOOTBALL_DATA_API_KEY=          # football-data.org (grátis, 10 req/min)
RAPIDAPI_KEY=                   # api-football backup (100 req/dia grátis)

# Rate Limits e Cache (CRÍTICOS)
MAX_REQUESTS_PER_MINUTE=10      # football-data.org limite
CACHE_TTL_CLASSIFICACAO=600     # 10 min (classificação)
CACHE_TTL_PREVISOES=3600        # 1 hora (previsões)
CACHE_TTL_MONTE_CARLO=3600      # 1 hora (probabilidades)
CACHE_TTL_SCOUTS=300            # 5 min (scouts)
CACHE_BACKEND=redis             # 'redis' ou 'memory' (prod = redis)

# Analytics & Monetização
GA_MEASUREMENT_ID=              # Google Analytics
ADSENSE_CLIENT_ID=              # Google AdSense (após aprovação)

# Monitoramento
SENTRY_DSN=                     # Sentry (errors Python/JS)
UPTIME_ROBOT_API_KEY=           # UptimeRobot (opcional)
\`\`\`

---

## 11. RISCOS E MITIGAÇÕES

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| API Cartola muda | Baixa | Alto | football-data.org como backup principal |
| Rate limit football-data.org | **Média-Alta** | Médio | **Cache 10min + backoff exponencial + circuit breaker + fallback dataset local** (CORE, não opcional) |
| FBref bloqueia scraping | Média | Baixo | Scouts Cartola são suficientes |
| AdSense recusa | Baixa | Médio | 30+ páginas, sem odds/apostas, linguagem 100% estatística |
| Monte Carlo lento | Baixa | Médio | Cache 1h, background job via scheduler |
| Classificação como "aposta" | Baixa | Alto | **Zero odds externas no MVP**, probabilidades 100% do modelo, linguagem: "projeção", "simulação", "cenários" |
| Uso de escudos/logos | Média | Médio | Tratar como conteúdo com copyright; usar crests da football-data.org API ou Wikimedia Commons; obter consentimento/licença quando necessário |
| Odds parecer aposta | Média | Alto | Sem links/CTA para bets; probabilidades só do modelo próprio; linguagem neutra ("projeção", não "palpite") |
| Dataset desatualizado | Baixa | Baixo | Verificar cobertura por temporada no build; complementar com APIs para temporada atual |

---

## 12. DIFERENCIAL COMPETITIVO

| Feature | Chance de Gol | GE/ESPN | ScoutDados |
|---------|---------------|---------|------------|
| Previsão placares | ✅ | ❌ | ✅ (top 5 + confiança) |
| Faixas de gols, ambos marcam (modelo próprio) | ❌ | ❌ | ✅ |
| Simulador interativo | ❌ | ❌ | ✅ |
| Ferramentas Cartola | ❌ | ❌ | ✅ |
| Visual moderno | ❌ | ✅ | ✅ |
| Mobile-first | ❌ | ✅ | ✅ |
| Monte Carlo | ✅ | ❌ | ✅ |
| Desfalques consolidados | ❌ | Parcial | ✅ |
| 100% gratuito | ✅ | ✅ | ✅ |
| Open API | ❌ | ❌ | ✅ (/docs) |

---

## 13. MONITORAMENTO E OBSERVABILIDADE

### 13.1 Rastreamento de Erros

**Sentry** (errors Python + JavaScript):
- Backend: `sentry_sdk.init()` em api_server.py
- Frontend: `Sentry.init()` em main.tsx
- Captura automática de exceções, stack traces, contexto de usuário
- Alertas via email/Slack quando taxa de erro > 5%

### 13.2 Uptime e Disponibilidade

**UptimeRobot** (free tier: 50 monitores):
- Endpoint `/health` do backend (a cada 5min)
- Endpoint `/api/status` (a cada 5min)
- Homepage `/` (a cada 5min)
- Alert se downtime > 2min consecutivos

### 13.3 Analytics de API

**Métricas por endpoint** (via middleware FastAPI):
- Req/min por rota
- Latência p50 / p95 / p99
- Taxa de erro 4xx / 5xx
- Cache hit rate
- Top 10 rotas mais lentas

**Dashboard customizado:**
\`\`\`python
GET /api/admin/metrics  # Métricas agregadas últimas 24h
{
  "total_requests": 12450,
  "avg_latency_ms": 245,
  "cache_hit_rate": 0.87,
  "error_rate": 0.02,
  "top_endpoints": [...]
}
\`\`\`

### 13.4 Alertas Críticos

| Condição | Ação |
|----------|------|
| football-data.org retorna 429 | Email + fallback automático para dataset local |
| Cache Redis inacessível | Log warning + fallback memory cache |
| Monte Carlo > 10s | Alert Sentry + reduzir para 5.000 simulações |
| Taxa erro > 10% | Email urgente + verificar logs |
| Downtime > 5min | SMS + investigar infra |

### 13.5 Logs Estruturados

\`\`\`python
import structlog

logger = structlog.get_logger()
logger.info("classificacao_obtida", fonte="football-data", cache_hit=True, latency_ms=87)
logger.warning("rate_limit_atingido", fonte="football-data", backoff_s=4)
logger.error("todas_fontes_falharam", tentativas=4, ultima_exc="TimeoutError")
\`\`\`

---

## 14. LINGUAGEM E POSICIONAMENTO (COMPLIANCE ADSENSE)

> Todo o conteúdo do site deve seguir linguagem de **estatística e simulação**, nunca de apostas.

| ✅ USAR | ❌ NUNCA USAR |
|---------|---------------|
| "Projeção estatística" | "Palpite certo" |
| "Simulação Monte Carlo" | "Aposte em..." |
| "Cenário mais provável" | "Odds" |
| "Modelo probabilístico" | "Casa de apostas" |
| "Confiança do modelo: 72%" | "Lucro garantido" |
| "Probabilidade calculada" | "Dica de aposta" |
| "Previsão baseada em dados" | Link/afiliado de bet |
| "Margem de erro: ±X%" | "Cupom", "bônus" |

**Disclaimer obrigatório em todas as páginas de previsão:**

> *"As projeções apresentadas são resultado de modelos estatísticos (Poisson, Monte Carlo) com fins informativos e educacionais. Não representam garantia de resultado e não devem ser utilizadas para fins de apostas."*

---

## 15. SEO DE VERDADE (ALÉM DE META TAGS)

### 15.1 Problema: SPA Puro Não Indexa Bem

React SPA renderiza no cliente → Google vê HTML vazio → SEO fraco.

### 15.2 Solução: SSR/SSG Híbrido

**Estratégia por tipo de página:**

| Página | Renderização | Ferramenta | Justificativa |
|--------|--------------|------------|---------------|
| `/blog/*` | **SSG** (build time) | Astro/Next | Conteúdo estático, indexação crítica |
| `/brasileirao` | **SSR** (server-side) | Astro + API | Dados dinâmicos, precisa estar fresco |
| `/cartola/*` | **SPA** (client-side) | React/Vite | Ferramentas interativas, não precisa indexar |
| `/sobre`, `/privacidade`, `/termos` | **SSG** | Astro/HTML | Páginas institucionais estáticas |

**Implementação sugerida:**
1. Manter React/Vite para `/cartola` (ferramenta interativa)
2. Adicionar Astro para `/blog` e `/brasileirao` (SEO crítico)
3. Astro consome mesma API FastAPI (reutilizar backend)

### 15.3 robots.txt

\`\`\`txt
# /public/robots.txt
User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/

Sitemap: https://scoutdados.com.br/sitemap.xml
\`\`\`

### 15.4 Sitemap Dinâmico

\`\`\`python
# api_server.py
@app.get("/sitemap.xml", response_class=Response)
async def sitemap():
    urls = [
        {"loc": "/", "changefreq": "daily", "priority": 1.0},
        {"loc": "/brasileirao", "changefreq": "hourly", "priority": 0.9},
        {"loc": "/cartola/dashboard", "changefreq": "daily", "priority": 0.8},
        {"loc": "/scouts", "changefreq": "daily", "priority": 0.8},
        # ... páginas blog (buscar do DB)
    ]
    xml = render_sitemap(urls)
    return Response(content=xml, media_type="application/xml")
\`\`\`

### 15.5 Meta Tags Estruturadas (Open Graph + Twitter Cards)

\`\`\`tsx
// Brasileirao.tsx
import { Helmet } from 'react-helmet-async';

<Helmet>
  <title>Classificação Brasileirão 2026 - Probabilidades em Tempo Real | ScoutDados</title>
  <meta name="description" content="Simulação de classificação com 10mil cenários Monte Carlo. Chances de título, Libertadores e rebaixamento atualizadas após cada rodada." />
  
  {/* Open Graph */}
  <meta property="og:title" content="Classificação Brasileirão 2026 - Probabilidades" />
  <meta property="og:description" content="Simulação Monte Carlo com chances de título, Liberta e rebaixamento" />
  <meta property="og:image" content="https://scoutdados.com.br/og-brasileirao.png" />
  <meta property="og:url" content="https://scoutdados.com.br/brasileirao" />
  
  {/* Twitter Card */}
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Classificação Brasileirão 2026" />
  <meta name="twitter:description" content="Probabilidades em tempo real" />
  <meta name="twitter:image" content="https://scoutdados.com.br/og-brasileirao.png" />
  
  {/* Canonical */}
  <link rel="canonical" href="https://scoutdados.com.br/brasileirao" />
</Helmet>
\`\`\`

### 15.6 Structured Data (JSON-LD)

\`\`\`tsx
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "ScoutDados",
  "description": "Estatísticas e previsões do Brasileirão e Cartola FC",
  "url": "https://scoutdados.com.br",
  "applicationCategory": "SportsApplication",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "BRL"
  }
}
</script>
\`\`\`

---

## 16. DECISÕES ARQUITETURAIS FIRMES

| Decisão | Justificativa |
|---------|---------------|
| **React+Vite para /cartola** | Stack ideal para dashboards/ferramentas interativas |
| **Astro para /blog e /brasileirao** | SSR/SSG para SEO real, consome mesma API |
| **Não migrar para WordPress** | WordPress = blog editorial; ScoutDados = ferramenta + dados |
| **Domínio separado do TecMestre** | Nichos diferentes (TI vs futebol), audiências distintas |
| **Zero odds no v1.0** | Probabilidades 100% do modelo, compliance AdSense |
| **football-data.org como fonte primária** | Melhor API gratuita com Série A, **cache+backoff+fallback como CORE (não opcional)** |
| **Dataset local para histórico** | Sem dependência de API para dados 2003-2024 |
| **Redis para cache em produção** | Memory cache apenas dev; prod precisa persistência |
| **Escudos via API quando possível** | football-data.org fornece crests; evitar scraping/copyright |

---

## 17. LEGAL E PRIVACIDADE (LGPD)

### 17.1 Política de Privacidade (/privacidade)

**Obrigatório mencionar:**

- ✅ **Cookies do Google Analytics** (GA4)
  - Finalidade: métricas de uso, origens de tráfego
  - Dados: páginas visitadas, tempo de sessão, dispositivo
  - Opt-out: via extensão do navegador

- ✅ **Dados do Google AdSense**
  - Cookies de publicidade (personalizada ou não)
  - Como desativar: Google Ad Settings

- ✅ **Endereço IP**
  - Armazenamento: anonimizado (últimos octetos mascarados)
  - Finalidade: prevenção de abuso (rate limiting), não geolocalização

- ✅ **Dados do Cartola FC**
  - ScoutDados não armazena login/senha
  - Apenas busca dados públicos via API Globo

- ✅ **Não vendemos dados**
  - Nenhum dado é compartilhado com terceiros além de Google (Analytics/AdSense)

### 17.2 Termos de Uso (/termos)

- Isenção de responsabilidade sobre previsões
- Proibição de uso para apostas
- Propriedade intelectual (código open source, conteúdo ©)
- Limitação de requisições à API (/docs)

### 17.3 Banner de Cookies (LGPD)

\`\`\`tsx
// Usar react-cookie-consent
import CookieConsent from "react-cookie-consent";

<CookieConsent
  location="bottom"
  buttonText="Aceitar"
  declineButtonText="Recusar"
  enableDeclineButton
  cookieName="scoutdados-consent"
>
  Usamos cookies do Google Analytics e AdSense para melhorar sua experiência.
  <a href="/privacidade">Saiba mais</a>
</CookieConsent>
\`\`\`

---

## 18. LICENÇA DE ESCUDOS E IMAGENS

### 18.1 Problema

Escudos de clubes são propriedade dos times/CBF. Scraping de imagens pode violar direitos autorais.

### 18.2 Solução

1. **Prioridade:** Usar escudos fornecidos pela API football-data.org (campo `crest`)
   - Exemplo: `GET /competitions/BSA/teams` retorna URL oficial do escudo

2. **Fallback:** Wikimedia Commons (licença livre)
   - Exemplo: https://commons.wikimedia.org/wiki/Category:Logos_of_Brazilian_football_clubs

3. **Último recurso:** API Cartola (já fornece URLs de escudos)

4. **NUNCA:** Fazer upload de escudos para o servidor sem verificar licença

### 18.3 Atribuição

No rodapé ou `/sobre`:
> *"Escudos e logos são propriedade de seus respectivos clubes. Dados fornecidos por API Cartola FC (Globo), football-data.org e fontes públicas."*

---

## 19. CACHE E CIRCUIT BREAKER (REQUISITO CORE)

### 19.1 Camada de Cache

**Em Produção: Redis obrigatório**

\`\`\`python
# config/settings.py
CACHE_BACKEND = os.getenv("CACHE_BACKEND", "redis")  # 'redis' ou 'memory'
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if CACHE_BACKEND == "redis":
    import redis
    cache_client = redis.from_url(REDIS_URL)
else:
    cache_client = {}  # dict simples (dev only)
\`\`\`

**Por que Redis em prod:**
- Cache compartilhado entre workers (Gunicorn multi-process)
- Persistência em disco (RDB/AOF)
- TTL nativo por chave
- Suporte a pub/sub (futuro: notificações)

### 19.2 Circuit Breaker

\`\`\`python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def buscar_football_data():
    # Se 5 falhas consecutivas → circuit OPEN por 60s
    # Durante OPEN → exceção imediata, sem fazer request
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.football-data.org/v4/...")
        response.raise_for_status()
        return response.json()
\`\`\`

**Comportamento:**
- Estado CLOSED (normal): requests passam
- 5 falhas → estado OPEN: requests falham imediatamente por 60s
- Após 60s → estado HALF_OPEN: tenta 1 request
  - Se OK → volta CLOSED
  - Se falha → volta OPEN por mais 60s

---

*ScoutDados.com.br — Versão 1.0 — Fevereiro 2026*
*Última atualização: 07/02/2026 23:45 — Revisão completa: dataset até 2024, monitoramento, SEO real, cache Redis, circuit breaker, LGPD, licença de escudos*
