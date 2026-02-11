import{m as e}from"./index-D32rddAo.js";/**
 * @license lucide-react v0.462.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i=e("Tag",[["path",{d:"M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z",key:"vktsd0"}],["circle",{cx:"7.5",cy:"7.5",r:".5",fill:"currentColor",key:"kqv944"}]]),s=[{slug:"monte-carlo-futebol",title:"Como funciona a simulação Monte Carlo no futebol",date:"2026-02-07",excerpt:"Entenda como usamos milhares de simulações para calcular as probabilidades de título, Libertadores e rebaixamento no Brasileirão.",tags:["Monte Carlo","Estatística","Brasileirão"],readTime:6,content:`## O que é Monte Carlo?

A simulação Monte Carlo é uma técnica estatística que usa milhares de cenários aleatórios para estimar probabilidades de eventos complexos. No contexto do futebol, ela responde perguntas como: **"Qual a chance do meu time ser campeão?"**

## Como aplicamos no Brasileirão

O ScoutDados simula os jogos restantes do campeonato **10.000 vezes**. Em cada simulação:

1. **Cada jogo restante é simulado** usando o modelo Poisson, que prevê a quantidade de gols de cada time baseado em força ofensiva, defensiva e mando de campo.
2. **A classificação final é calculada** somando os pontos reais com os simulados.
3. **Os resultados são agregados** — se um time ficou em 1º em 1.820 de 10.000 simulações, sua probabilidade de título é 18,2%.

## O modelo Poisson por trás

Para simular um jogo, usamos a distribuição de Poisson, que modela a probabilidade de um número de gols dado uma média esperada (λ):

$$P(X = k) = \\frac{e^{-\\lambda} \\cdot \\lambda^k}{k!}$$

Onde **λ** (lambda) é a média de gols esperada, calculada a partir de:

- **Força ofensiva** do mandante (gols marcados / média da liga)
- **Força defensiva** do visitante (gols sofridos / média da liga)
- **Fator casa** (historicamente ~1.3x no Brasileirão)

## Exemplo prático

Se o Flamengo (ataque forte, λ = 1.8) joga em casa contra o Cuiabá (defesa fraca), simulamos:

- Gols do Flamengo: sorteio Poisson(λ=1.8)
- Gols do Cuiabá: sorteio Poisson(λ=0.7)
- Resultado: 2x0, 1x1, 3x1... cada simulação dá um placar diferente

Repetindo isso para **todos os jogos restantes**, 10.000 vezes, temos uma distribuição estatística robusta.

## Limitações

- **Não prevê o futuro.** Monte Carlo calcula probabilidades baseadas no desempenho passado.
- **Surpresas acontecem.** Times podem melhorar/piorar, contratar, perder jogadores.
- **Atualizamos após cada rodada** para incorporar os resultados mais recentes.

## No ScoutDados

Acesse a página [Brasileirão](/brasileirao) para ver as probabilidades em tempo real: título, G4 (Libertadores), G8 (Sul-Americana) e Z4 (rebaixamento) para todos os 20 times.

*As projeções são resultado de modelos estatísticos com fins informativos e educacionais. Não representam garantia de resultado.*`},{slug:"xg-expected-goals",title:"xG explicado: o que é Expected Goals e como usar",date:"2026-02-06",excerpt:"Expected Goals (xG) é a métrica que revolucionou a análise de futebol. Saiba como funciona e por que um time pode jogar 'bem' e perder.",tags:["xG","Estatística","Análise"],readTime:5,content:`## O que é xG?

**Expected Goals (xG)** mede a qualidade das chances de gol criadas. Cada finalização recebe um valor entre 0 e 1, representando a probabilidade de virar gol baseado em dados históricos.

## Como é calculado?

Cada chute é avaliado por fatores como:

- **Distância do gol** — chutes de fora da área valem ~0.03 xG
- **Ângulo** — chutes de dentro da área com ângulo aberto valem ~0.15-0.40 xG
- **Tipo de jogada** — penalti = 0.76 xG, contra-ataque = mais alto que jogada parada
- **Parte do corpo** — cabeça vs pé

## Por que xG importa?

O placar mente, o xG não. Exemplos:

| Jogo | Placar | xG |
|------|--------|----|
| Time A 1x0 Time B | A venceu | A: 0.8 xG, B: 2.3 xG |
| Time C 0x0 Time D | Empate | C: 3.1 xG, D: 0.4 xG |

No primeiro caso, o Time B foi **melhor** — criou mais e melhores chances. A longo prazo, times com xG alto tendem a converter os resultados.

## xG no ScoutDados

Usamos xG para:

- **Previsão de placares** — nosso modelo Poisson usa médias de xG como λ para cada time
- **Confrontos** — mostramos xG esperado de cada time no card de previsão
- **Identificar surpresas** — times com desempenho muito acima/abaixo do xG tendem a regredir à média

## Onde ver

Na página de [Confrontos](/confrontos), cada card de jogo mostra o xG esperado para mandante e visitante, calculado pelo nosso modelo.

*As projeções são resultado de modelos estatísticos com fins informativos e educacionais. Não representam garantia de resultado.*`},{slug:"classificacao-brasileirao-2026",title:"Classificação do Brasileirão 2026: probabilidades em tempo real",date:"2026-02-05",excerpt:"Acompanhe a classificação do Brasileirão 2026 com probabilidades de título, Libertadores e rebaixamento atualizadas a cada rodada.",tags:["Brasileirão","Classificação","Monte Carlo"],readTime:4,content:`## Classificação ao vivo com probabilidades

O ScoutDados oferece a classificação do Brasileirão 2026 com colunas extras que nenhum outro site gratuito mostra de forma tão completa:

| Coluna | O que significa |
|--------|-----------------|
| **Prob. Título** | Chance de terminar em 1º lugar |
| **Prob. Liberta** | Chance de ficar no G4-G6 (vaga direta/fase preliminar) |
| **Prob. Sula** | Chance de ficar entre G7-G8 (Sul-Americana) |
| **Prob. Rebaixa** | Chance de cair para a Série B (Z4) |

## Como calculamos

Cada probabilidade vem de **10.000 simulações Monte Carlo**:

1. Pegamos a classificação atual (pontos, saldo de gols)
2. Simulamos todos os jogos restantes usando nosso modelo Poisson
3. Contamos quantas vezes cada time terminou em cada faixa
4. Dividimos pelo total de simulações

## Quando atualiza?

As probabilidades são recalculadas automaticamente após o encerramento de cada rodada. O scheduler do ScoutDados roda o Monte Carlo em background e salva em cache, então a página carrega instantaneamente.

## Pontos de corte históricos

Baseado nos últimos 20 anos do Brasileirão:

| Objetivo | Pontos típicos |
|----------|---------------|
| Título | 78-85 pts |
| G4 (Libertadores) | 63-68 pts |
| G8 (Sul-Americana) | 52-56 pts |
| Escapar rebaixamento | 45-48 pts |

## Acompanhe

Acesse [Brasileirão](/brasileirao) para ver a tabela completa com todas as probabilidades, atualizada em tempo real.

*As projeções são resultado de modelos estatísticos com fins informativos e educacionais. Não representam garantia de resultado.*`},{slug:"guia-cartola-fc-2026",title:"Guia completo do Cartola FC 2026: como montar o melhor time",date:"2026-02-04",excerpt:"Tudo o que você precisa saber para mandar bem no Cartola FC 2026: escalação, valorização, MPV, capitão e estratégias avançadas.",tags:["Cartola FC","Escalação","Guia"],readTime:8,content:`## O básico do Cartola FC

O Cartola FC é o fantasy game oficial do Brasileirão, onde você monta um time virtual com jogadores reais e pontua de acordo com o desempenho deles em campo.

### Regras fundamentais:

- **Orçamento:** C$ 100,00 iniciais
- **Escalação:** 12 jogadores (1 goleiro + 10 de linha + 1 técnico)
- **Limite por clube:** máximo 5 jogadores do mesmo time
- **Capitão:** 1 jogador com pontuação multiplicada por 1.5x

## Dois times por rodada: a estratégia que funciona

O ScoutDados gera **dois times otimizados** para cada rodada:

### Time de Valorização (C$)
- Foco em jogadores baratos (C$ 3-6) com alto potencial de valorizar
- Usa o cálculo de **MPV (Mínimo para Valorizar)**: o jogador precisa pontuar acima de um limiar para subir de preço
- Ideal para início de campeonato — acumula patrimônio rápido

### Time de Pontuação
- Foco em jogadores caros com média alta e bons confrontos
- Capitão no jogador com maior projeção de pontos
- Ideal para quando você já tem patrimônio alto e quer subir no ranking

## O que é MPV?

O **Mínimo para Valorizar** é um cálculo proprietário do ScoutDados:

$$MPV \\approx 0.55 \\times Preço^{1.15}$$

Se um jogador custa C$ 5.00, ele precisa pontuar pelo menos **~3.2 pontos** para valorizar. Jogadores baratos precisam de menos pontos — por isso são ideais para o time de valorização.

## Scouts que mais impactam

| Scout | Pontos | Importância |
|-------|--------|------------|
| Gol (G) | +8.0 | ⭐⭐⭐ |
| Assistência (A) | +5.0 | ⭐⭐⭐ |
| Saldo de Gol (SG) | +5.0 | ⭐⭐ (só goleiros/defensores) |
| Finalização na Trave (FT) | +3.0 | ⭐⭐ |
| Desarme (DS) | +1.2 | ⭐ (volume) |
| Cartão Amarelo (CA) | -1.0 | ❌ |
| Gol Contra (GC) | -3.0 | ❌❌ |

## Como usar o ScoutDados

1. Acesse o [Dashboard](/dashboard) para ver o panorama geral
2. Vá para [Escalação](/escalacao) para gerar seus dois times
3. Confira os [Confrontos](/confrontos) para validar os jogos
4. Acompanhe os [Scouts](/scouts) para ver quem está pontuando

## Dicas avançadas

- **Evite jogadores de times que jogam contra defesas fortes** — o confronto importa mais que a média do jogador
- **Goleiros de times que jogam fora** raramente fazem SG — prefira mandantes
- **Técnicos pontuam pela média do time** — escale técnicos de times favoritos

*O ScoutDados é uma ferramenta de simulação e estatística. O Cartola FC é marca registrada da Globo.*`},{slug:"modelo-poisson-previsao-placares",title:"Previsão de placares: como funciona nosso modelo Poisson",date:"2026-02-03",excerpt:"Nosso modelo usa distribuição de Poisson para prever placares. Entenda a matemática por trás e veja como os top 5 placares mais prováveis são calculados.",tags:["Poisson","Previsão","Estatística"],readTime:7,content:`## Por que Poisson?

A distribuição de Poisson modela eventos discretos que ocorrem em um intervalo — como **gols em uma partida de futebol**. Desde os anos 1950, pesquisadores como Moroney (1956) demonstraram que gols no futebol seguem bem essa distribuição.

## A fórmula

$$P(X = k) = \\frac{e^{-\\lambda} \\cdot \\lambda^k}{k!}$$

Onde:
- **X** = número de gols
- **k** = 0, 1, 2, 3, 4...
- **λ** = média de gols esperada (taxa)

## Como calculamos λ para cada time

Para um jogo entre **Time A (casa)** vs **Time B (fora)**:

$$\\lambda_A = \\text{Ataque}_A \\times \\text{Defesa}_B \\times \\text{Média da Liga} \\times \\text{Fator Casa}$$

$$\\lambda_B = \\text{Ataque}_B \\times \\text{Defesa}_A \\times \\text{Média da Liga}$$

Onde:
- **Ataque** = gols marcados pelo time / média de gols marcados na liga
- **Defesa** = gols sofridos pelo adversário / média de gols sofridos na liga
- **Fator Casa** = ~1.3 (vantagem média do mandante no Brasileirão)

## Exemplo: Flamengo vs Cuiabá

Suponha:
- λ Flamengo (casa) = 1.85
- λ Cuiabá (fora) = 0.72

Probabilidades de gols do Flamengo:

| Gols | Probabilidade |
|------|---------------|
| 0 | 15.7% |
| 1 | 29.1% |
| 2 | 26.9% |
| 3 | 16.6% |
| 4+ | 11.7% |

## Top 5 placares mais prováveis

Combinamos as distribuições de cada time para obter a probabilidade de cada placar:

| Placar | Probabilidade |
|--------|---------------|
| 2x0 | 13.8% |
| 1x0 | 12.9% |
| 2x1 | 10.7% |
| 1x1 | 8.4% |
| 3x0 | 7.2% |

## Métricas derivadas

A partir da distribuição de Poisson, calculamos:

- **Vitória / Empate / Derrota** — somando as probabilidades de todos os placares possíveis onde casa ganha, empata ou perde
- **Faixas de gols** — P(total ≤ 1), P(total 2-3), P(total ≥ 4)
- **Ambos marcam** — P(gols_casa > 0 E gols_fora > 0)
- **Confiança** — baseada na diferença entre as médias ofensivas/defensivas e no histórico recente

## V3: além do Poisson puro

Nosso modelo V3 (ScorePredictor) incorpora:

- **Frequências contextuais** — ajustes baseados em jogos recentes (últimas 5 rodadas)
- **H2H (head-to-head)** — histórico de confrontos diretos
- **Desfalques** — jogadores lesionados/suspensos impactam o λ
- **Forma recente** — times em sequência positiva/negativa recebem ajuste

Tudo isso alimenta a página de [Confrontos](/confrontos), onde cada jogo mostra os top 5 placares, probabilidades 1x2, faixas de gols e confiança do modelo.

*As projeções são resultado de modelos estatísticos com fins informativos e educacionais. Não representam garantia de resultado.*`}];function t(a){return s.find(o=>o.slug===a)}export{i as T,t as g,s as p};
