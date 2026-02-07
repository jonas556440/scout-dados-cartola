# 🏆 Cartola FC 2026 - Sistema de Escalação Inteligente

Sistema completo para análise e geração de escalações otimizadas do Cartola FC 2026.

## 📋 Funcionalidades

### 🎯 Dois Times por Rodada
1. **Time Valorização** - Foco em jogadores baratos que vão valorizar
2. **Time Pontuação** - Foco em maximizar pontos da rodada

### ⚽ NOVO v3: Análise de Confrontos (como sites especializados!)
- **Adversário da rodada**: Força ofensiva/defensiva de cada time
- **Mando de campo**: Casa vs Fora (times em casa pontuam ~30% mais)
- **Chance de SG**: Probabilidade de não sofrer gols (importante para defensores)
- **Expectativa de gols**: Quantos gols o time deve fazer (importante para atacantes)
- **Forma recente**: Últimos 5 jogos do time

### 💰 Sistema de Patrimônio
- Acompanhamento de cartoletas por rodada
- Evolução separada para cada tipo de time
- Histórico completo de escalações e resultados
- A cada rodada, usa as cartoletas disponíveis (ganhos de valorização!)

### 📊 Fontes de Dados
- **API Oficial Cartola FC**: `https://api.cartola.globo.com`
  - `/atletas/mercado` - Lista todos jogadores com preços e status
  - `/mercado/status` - Status do mercado (aberto/fechado)
  - `/atletas/pontuados` - Scouts/pontuação após rodada
  - `/partidas/{rodada}` - **NOVO**: Partidas para análise de confrontos
  
- **Estatísticas Avançadas** (opcional):
  - `soccerdata` - FBref, Sofascore, Understat
  - xG (Expected Goals), xA (Expected Assists)
  - Métricas defensivas e de forma

### 🧠 Algoritmos de Seleção v3

#### Time de Pontuação
Usa **Score de Potencial** com análise de confrontos:
- **Qualidade do jogador (30%)**: Média ou preço como proxy
- **Confronto da rodada (35%)**: Adversário, mando, SG, gols esperados
- **Posição ofensiva (15%)**: ATA/MEI pontuam mais
- **Risco/Tendência (20%)**: Cartões, contusões, forma

#### Time de Valorização
- Preço baixo (25%) + Tendência (25%) + Confronto (25%) + Margem (15%) + Risco (10%)

### 🗄️ Banco de Dados
- SQLite para armazenamento local
- Histórico completo de scouts por rodada
- Evolução de preços e patrimônio
- Estatísticas por time e posição

## 🚀 Instalação

```bash
cd cartolafc2026
pip install -r requirements.txt

# Opcional: estatísticas avançadas
pip install soccerdata
```

## 💻 Uso

### Modo Interativo
```bash
python main.py
```

### Comandos Principais
```bash
# Ver status do mercado
python main.py status

# NOVO v3: Analisar confrontos da rodada
python main.py confrontos

# Gerar times otimizados (com análise de confrontos!)
python main.py escalar -e 4-4-2

# Salvar times no histórico (usa cartoletas atuais!)
python main.py salvar -e 4-4-2

# Ver evolução do patrimônio
python main.py patrimonio

# Registrar resultado após rodada
python main.py resultado

# Ver histórico de escalações
python main.py historico
```

### Fluxo Típico por Rodada
1. `status` - Verificar se mercado está aberto
2. **`confrontos`** - NOVO! Ver análise detalhada dos jogos
3. `escalar -e 4-4-2` - Gerar times otimizados
4. `salvar -e 4-4-2` - Salvar escalação oficial
5. (após rodada encerrar)
6. `resultado` - Registrar pontuação real
7. `patrimonio` - Ver evolução das cartoletas

### Exemplo de Saída do Comando `confrontos`
```
🟢 TIMES PARA ESCALAR (confrontos favoráveis):
  1. VIT 🏠 vs REM | SG: 82% | Gols: 1.1 | Score: 86
  2. INT 🏠 vs CAP | SG: 92% | Gols: 1.2 | Score: 72

🔴 TIMES PARA EVITAR (confrontos difíceis):
  ⚠️ BAH ✈️ vs COR | Dificuldade: MUITO DIFÍCIL | Score: 4

🛡️ MELHORES PARA SG (defensores):
  • FLA ✈️ vs SAO | Chance SG: 96%

⚽ MELHORES PARA GOLS (atacantes/meias):
  • INT 🏠 vs CAP | Expectativa: 1.2 gols
```

## 📁 Estrutura do Projeto

```
cartolafc2026/
├── src/
│   ├── api/
│   │   └── cartola_api.py           # Cliente da API oficial
│   ├── database/
│   │   ├── models.py                # Modelos SQLAlchemy
│   │   ├── db_manager.py            # Gerenciador do banco
│   │   └── history_manager.py       # Histórico e patrimônio
│   ├── analysis/
│   │   ├── mpv_calculator.py        # Cálculo do MPV
│   │   ├── team_selector.py         # Seleção de times v3
│   │   ├── match_analyzer.py        # NOVO: Análise de confrontos
│   │   ├── confrontos_analyzer.py   # NOVO: Relatórios de confrontos
│   │   ├── stats_analyzer.py        # Análise estatística
│   │   └── statistics_provider.py   # Fontes de estatísticas externas
│   ├── scrapers/
│   │   └── scout_collector.py       # Coleta de scouts pós-rodada
│   └── utils/
│       └── helpers.py               # Funções auxiliares
├── data/
│   ├── cartola.db              # Banco SQLite
│   └── backups/                # Backups do banco
├── tests/
│   └── test_*.py               # Testes unitários
├── config/
│   └── settings.py             # Configurações
├── requirements.txt
├── main.py                     # Ponto de entrada
└── README.md
```

## � Análise da Estratégia

**✅ ESTRATÉGIA VALIDADA COM DADOS REAIS!**

Nossa análise da rodada 1 confirmou:
- ✅ Sweet Spot C$3-6 valorizou **+127% A MAIS** que C$10+
- ✅ C$6-10 tem **melhor custo-benefício** (0.65 pts/cartoleta)
- ✅ Sistema funcionando perfeitamente na rodada 2

📚 **Ver análise completa**: [ANALISE_VALIDACAO.md](ANALISE_VALIDACAO.md)  
📊 **Dados detalhados**: [docs/ANALISE_ESTRATEGIA_RODADAS.md](docs/ANALISE_ESTRATEGIA_RODADAS.md)

---

## �💻 Execução

### 🚀 Serviços Systemd (Recomendado)

**Backend (porta 8000):**
```bash
sudo systemctl status cartolafc-backend.service   # Ver status
sudo systemctl restart cartolafc-backend.service  # Reiniciar
sudo journalctl -u cartolafc-backend.service -f   # Logs
```

**Frontend (porta 5176):**
```bash
cd frontend && bun run build                       # Build frontend
/usr/local/lsws/bin/lswsctrl restart               # Reiniciar OpenLiteSpeed
```

📚 **Ver guia completo**: [SERVICOS.md](SERVICOS.md) | [docs/EXECUCAO.md](docs/EXECUCAO.md)

### 🔍 Verificar se está funcionando

```bash
python3 healthcheck.py
# ou
curl http://localhost:8000/api/status
```

## 📈 Estratégia de Valorização

Baseado nas dicas oficiais do Gato Mestre:
- Priorizar jogadores abaixo de C$10
- Foco em jogadores "prováveis" (status 7)
- Evitar defesa completa do mesmo time
- Técnico barato nas primeiras rodadas

## 🔄 Fluxo de Trabalho

1. **Antes da Rodada**: Atualiza mercado e gera escalações
2. **Após a Rodada**: Coleta scouts e atualiza banco
3. **Análise Contínua**: Melhora algoritmos com dados históricos

## 📊 Scouts e Pontuação

| Scout | Pontos | Descrição |
|-------|--------|-----------|
| G     | +8.0   | Gol |
| A     | +5.0   | Assistência |
| SG    | +5.0   | Saldo de Gols (defesa) |
| FS    | +0.5   | Falta Sofrida |
| FF    | +0.8   | Finalização para Fora |
| FD    | +1.2   | Finalização Defendida |
| FT    | +3.0   | Finalização na Trave |
| DS    | +1.5   | Desarme |
| RB    | +1.5   | Roubada de Bola |
| DD    | +3.0   | Defesa Difícil |
| DP    | +7.0   | Defesa de Pênalti |
| CA    | -1.0   | Cartão Amarelo |
| CV    | -3.0   | Cartão Vermelho |
| GC    | -3.0   | Gol Contra |
| PP    | -4.0   | Pênalti Perdido |
| PC    | -1.0   | Pênalti Cometido |
| FC    | -0.3   | Falta Cometida |
| GS    | -1.0   | Gol Sofrido (goleiro) |
| I     | -0.1   | Impedimento |
| PI    | -0.1   | Passe Incompleto |

## 🛠️ Tecnologias

- Python 3.10+
- SQLAlchemy (ORM)
- Requests (HTTP)
- Pandas (Análise de dados)
- Schedule (Agendamento)
- Rich (Interface CLI)

## 📄 Licença

MIT License - Uso livre para fins pessoais
