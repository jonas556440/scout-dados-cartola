# 🗂️ ESTRUTURA DETALHADA DO PROJETO

## 📁 Diretórios e Arquivos Principais

```
/www/wwwroot/scoutdados.com.br/
│
├── 📘 DOCUMENTAÇÃO
│   ├── ANALISE_COMPLETA_APLICACAO.md      ⭐ Análise 400+ linhas
│   ├── TOP3_PRIORIDADES.md                ⭐ O que fazer agora
│   ├── README.md
│   ├── ROADMAP_LANCAMENTO.md
│   ├── .github/copilot-instructions.md
│   └── docs/
│       ├── INTEGRACAO_FRONTEND.md
│       ├── RESILIENCIA.md
│       └── CORRECAO_DASHBOARD.md
│
├── 🐍 BACKEND (Python/FastAPI)
│   ├── api_server.py                      ⭐ 1255 linhas - Principal
│   ├── main.py                            CLI interativo
│   ├── scheduler_service.py               Agendador (APScheduler)
│   │
│   ├── src/
│   │   ├── api/
│   │   │   └── cartola_api.py            Cliente API Cartola com cache
│   │   │
│   │   ├── analysis/                      🧠 Algoritmos inteligentes
│   │   │   ├── mpv_calculator.py         MPV = Melhor Preço × Valor
│   │   │   ├── team_selector.py          Seleção de times (2 estratégias)
│   │   │   ├── match_analyzer.py         Força ofensiva/defensiva
│   │   │   ├── confrontos_analyzer.py    Análise de confrontos
│   │   │   ├── score_predictor.py        Predição de pontos
│   │   │   └── statistics_provider.py    Estatísticas externas
│   │   │
│   │   ├── database/
│   │   │   ├── models.py                 SQLAlchemy models
│   │   │   ├── db_manager.py             Gerenciador do banco
│   │   │   ├── history_manager.py        Histórico e patrimônio
│   │   │   └── cartola.db               SQLite (5MB)
│   │   │
│   │   ├── scrapers/
│   │   │   └── scout_collector.py       Coleta de dados
│   │   │
│   │   └── utils/
│   │       └── helpers.py                Funções auxiliares
│   │
│   ├── config/
│   │   └── settings.py                   Configurações globais
│   │
│   ├── requirements.txt                  Dependências Python
│   └── requirements_api.txt
│
├── ⚛️ FRONTEND (React/TypeScript)
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html                        ⭐ SEO + Meta tags
│   ├── .env
│   │
│   ├── src/
│   │   ├── main.tsx                      Entry point
│   │   ├── App.tsx                       Router principal
│   │   │
│   │   ├── pages/                        🔗 7 páginas
│   │   │   ├── LandingPage.tsx           / - Página inicial
│   │   │   ├── Dashboard.tsx             /dashboard - Stats
│   │   │   ├── Escalacao.tsx             /escalacao - Gerar times
│   │   │   ├── Confrontos.tsx            /confrontos - Análise jogos
│   │   │   ├── Mercado.tsx               /mercado - Jogadores
│   │   │   ├── Historico.tsx             /historico - Escalações
│   │   │   ├── Estatisticas.tsx          /estatisticas - Stats
│   │   │   ├── Sobre.tsx                 /sobre - Info projeto
│   │   │   └── NotFound.tsx              404
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── MainLayout.tsx        Layout principal
│   │   │   │   └── Navigation.tsx        Navbar
│   │   │   │
│   │   │   └── cartola/
│   │   │       ├── PlayerCard.tsx        ⭐ Mostra pontos + %
│   │   │       ├── FormationDisplay.tsx  Visualiza time
│   │   │       ├── MatchCard.tsx         Confronto
│   │   │       ├── StatCard.tsx          Estatística
│   │   │       ├── PositionBadge.tsx     Badge posição
│   │   │       └── ... (15+ componentes)
│   │   │
│   │   ├── hooks/
│   │   │   └── useCartolaApi.ts          ⭐ React Query hooks
│   │   │       - useDashboard()
│   │   │       - useEscalacao()
│   │   │       - useConfrontos()
│   │   │       - useMercado()
│   │   │       - useHistorico()
│   │   │
│   │   ├── types/
│   │   │   └── cartola.ts                ⭐ Tipos TypeScript
│   │   │       - Player, Team, Match, etc
│   │   │
│   │   ├── lib/
│   │   │   ├── utils.ts                  Funções utilitárias
│   │   │   └── persistor.ts              localStorage helper
│   │   │
│   │   ├── data/
│   │   │   └── mockData.ts               Dados para testes
│   │   │
│   │   └── styles/
│   │       └── globals.css               Tailwind + custom
│   │
│   ├── dist/                             Build production
│   │   ├── index.html
│   │   ├── assets/
│   │   │   ├── index-*.js
│   │   │   └── index-*.css
│   │   ├── favicon.ico
│   │   └── og-image.png
│   │
│   └── public/
│       └── favicon.ico
│
├── 🔧 CONFIGURAÇÃO
│   ├── .htaccess                         Apache rewrite rules
│   ├── .user.ini                         PHP config
│   ├── robots.txt                        SEO - crawlers
│   ├── deploy_production.sh               Script deploy
│   ├── setup.py                          Setup completo
│   ├── setup_full.sh                     Setup bash
│   └── setup_astro_blog.sh               Blog setup
│
├── 📊 SYSTEMD SERVICES
│   ├── scoutdados-api.service            FastAPI backend
│   ├── cartolafc-scheduler.service       Agendador
│   └── cartolafc-frontend.service        React dev
│
├── 🌐 PROXY REVERSO (OpenLiteSpeed)
│   └── /www/server/panel/vhost/openlitespeed/
│       └── proxy/scoutdados.com.br/
│           ├── api.conf                  Proxy /api → :8000
│           └── urlrewrite/
│               ├── spa.conf              SPA routing
│               └── security.conf         Bloqueia .py, .db, .sql
│
├── 📁 DATA & LOGS
│   ├── data/
│   │   ├── cartola.db                    SQLite database
│   │   └── backups/
│   │
│   └── logs/
│       ├── scheduler.log
│       └── api_errors.log
│
└── 📄 OUTROS
    ├── .gitignore
    ├── cartolafc.db                      Backup database
    ├── favicon.ico
    └── index.html                        Home (antes do build)
```

---

## 🔄 FLUXO DE DADOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    USUÁRIO VISITA SITE                          │
│                   https://scoutdados.com.br                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Landing Page   │
                    │   (Hero + FAQ)  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
       Clica em      Clica em         Clica em
     "Gerar Time"   "Dashboard"    "Confrontos"
            │                │                │
      ┌─────▼─────┐    ┌─────▼─────┐    ┌────▼─────┐
      │ Escalacao │    │ Dashboard │    │Confrontos│
      └─────┬─────┘    └─────┬─────┘    └────┬─────┘
            │                │               │
            └────────────────┼───────────────┘
                             │
            ┌────────────────▼────────────────┐
            │   React Query Hook Trigger      │
            │   (useEscalacao/useDashboard)   │
            └────────────┬─────────────────────┘
                         │
                  ┌──────▼──────┐
                  │  Cache Hit? │
                  └──────┬──────┘
                    ┌────┴────┐
                  SIM        NÃO
                    │         │
            ┌───────▼──┐  ┌───▼──────────┐
            │ Usar     │  │ Requisição   │
            │ Cache    │  │ HTTP à API   │
            └───────┬──┘  └───┬──────────┘
                    │         │
                    │    ┌────▼────────────────┐
                    │    │ Backend FastAPI    │
                    │    │ /api/escalacao     │
                    │    │ /api/dashboard     │
                    │    └────┬───────────────┘
                    │         │
                    │    ┌────▼─────────────────────┐
                    │    │ Processar:               │
                    │    │ 1. Carregar Mercado      │
                    │    │ 2. Chamar API Cartola    │
                    │    │ 3. MPVCalculator         │
                    │    │ 4. TeamSelector          │
                    │    │ 5. MatchAnalyzer         │
                    │    │ 6. Gerar resposta JSON   │
                    │    └────┬─────────────────────┘
                    │         │
                    │    ┌────▼──────────────┐
                    │    │ Banco de Dados   │
                    │    │ SQLite           │
                    │    │ (cache + history)│
                    │    └────┬──────────────┘
                    │         │
                    └─────┬───┘
                          │
            ┌─────────────▼──────────────┐
            │   Frontend Recebe JSON     │
            │   React Query Caches       │
            └─────────────┬──────────────┘
                          │
            ┌─────────────▼──────────────┐
            │   Renderizar Componentes   │
            │   - PlayerCard (mostra pts)│
            │   - FormationDisplay       │
            │   - StatCard               │
            └─────────────┬──────────────┘
                          │
            ┌─────────────▼──────────────┐
            │   Exibir na Tela           │
            │   (Animações + Transições) │
            └────────────────────────────┘
```

---

## 🎯 ALGORITMOS PRINCIPAIS

### MPV Calculator
```
ENTRADA: Atleta com dados (preço, média, etc)
         Confronto (adversário, mando, etc)

PROCESSO:
1. score_preço = (6 - preço) × 10              // Quanto mais barato, mais pontos
2. score_media = (média - 5) × 2               // Acima de 5 é bom
3. score_confronto = força_adversário × peso   // Jogo fácil = mais pontos
4. score_tendencia = variacao_pct × 1.5        // Tendência positiva

MPV_FINAL = (score_preço × 0.35) +
            (score_media × 0.25) +
            (score_confronto × 0.25) +
            (score_tendencia × 0.15)

SAÍDA: Score 0-100 (quanto maior = melhor oportunidade)
```

### Team Selector
```
ESTRATÉGIA 1: VALORIZAÇÃO
- Foco em jogadores C$2-6 com tendência positiva
- Buscar outliers que vão valorizar
- Risco: Podem não jogar

ESTRATÉGIA 2: PONTUAÇÃO
- Foco em jogadores com média alta
- Considerar confrontos favoráveis
- Risco: Custos podem ser altos

PROCESSO:
1. Gerar 2 times diferentes (Val + Pont)
2. Validar formação (1 GOL + 10 linha + 1 TEC)
3. Respeitar limite orçamento
4. Reservas (5 back-ups)
5. Escolher capitão
```

---

## 📡 ENDPOINTS DA API

```
GET  /api/status                    Status mercado + rodada
GET  /api/mercado/atletas           500+ jogadores (2-3s)
GET  /api/confrontos/analise        Análise partidas
POST /api/escalacao/gerar           Gera 2 times
GET  /api/dashboard                 Dashboard stats
GET  /api/atletas/{id}              Detalhes jogador
GET  /api/historico                 Escalações passadas
POST /api/cache/limpar              Force refresh

Todos retornam JSON
Suportam CORS
Têm retry automático 3x
Timeout: 15s
Cache: 5 minutos
```

---

## 🚀 DEPLOYMENT

```
┌──────────────────────────────────────┐
│     GitHub (Versionamento)           │
└─────────────────┬────────────────────┘
                  │
         git push origin main
                  │
        ┌─────────▼────────────┐
        │ CI/CD (GitHub Actions)│  ← TODO
        │ - Testes automatizados│
        │ - Lint               │
        │ - Build              │
        └─────────┬────────────┘
                  │
        ┌─────────▼──────────────┐
        │ Deploy na Produção     │
        │ - SSH para servidor    │
        │ - Pull code            │
        │ - npm run build        │
        │ - restart service      │
        └─────────┬──────────────┘
                  │
        ┌─────────▼──────────────┐
        │ Resultado em Produção  │
        │ https://scoutdados.com │
        └────────────────────────┘
```

---

## 💾 BANCO DE DADOS (SQLite)

```
Tables:
- players          500+ registros
- teams            Escalações salvas
- matches          Partidas do campeonato
- scouts           Pontuações por rodada
- patrimony        Evolução cartoletas

Queries rápidas:
SELECT * FROM players WHERE price < 10 AND tendency > 0
→ ~50ms

Backups automáticos
Via scheduler_service.py a cada rodada
```

---

## 🔐 Segurança Implementada

```
✅ HTTPS/SSL (Cloudflare)
✅ CORS configurado
✅ Input validation (Pydantic)
✅ SQL injection prevention
✅ Rate limiting via nginx
✅ Bloquear .py, .db, .sql

❌ TODO:
- Autenticação/Login
- CSRF tokens
- WAF rules
- DDoS protection
```

---

## 📊 Performance Atual

```
Frontend:
- Bundle size: 1.0MB (gzip: 292KB)
- Carregamento: ~2s (primeira visita)
- Interatividade: <100ms
- Mobile: Responsivo 100%

Backend:
- Dashboard: ~1.5s
- Escalação: ~2.5s
- Mercado: ~1.2s
- Uptime: 99.9%

Database:
- Queries: <100ms
- Tamanho: 5MB
- Backups: Automáticos
```

---

## 🎓 ARQUITETURA PATTERNS

```
✅ Component-based (React)
✅ Custom hooks (React Query)
✅ Separation of concerns
✅ Type-safe (TypeScript)
✅ API-driven
✅ Event-driven (Redis future)
✅ Immutable updates
✅ Optimistic updates (future)

❌ TODO:
- Redux/Zustand
- Microservices
- Message queues
- Event streaming
```

---

Este é o mapa visual completo da aplicação. Use como referência para navegar pelo código!
