# 🎯 Auditoria UX/UI - ScoutDados
**Data:** 7 de Fevereiro de 2026  
**Objetivo:** Tornar o app **autoexplicativo para público leigo**

---

## 📊 Status Atual dos 20 Times
✅ **CONFIRMADO:** Todos os 20 times do Brasileirão 2026 estão mapeados corretamente:
- Backend (TEAM_SLUGS): 24 slugs (20 times + 4 aliases)
- Frontend (ABREV_TO_SLUG): 24 mapeamentos
- Blog (TIMES_MAP): 25 entradas (20 times + 5 aliases)
- Sitemap: 24 URLs de times

---

## 🚨 Problemas Críticos Identificados

### 1. **Links Clicáveis Invisíveis** (PRIORIDADE ALTA)
**Problema:** Na tabela de classificação, nomes dos times são clicáveis mas não parecem links.
- ❌ Sem cor diferenciada
- ❌ Sem cursor pointer visível
- ❌ Sem tooltip explicativo
- ❌ hover:underline só aparece ao passar mouse (CSS puro)

**Impacto:** Usuários não descobrem que podem clicar para ver detalhes do time.

**Solução:**
```tsx
// ❌ ATUAL (linha 174)
<div className="font-semibold text-sm hover:underline">{time.nome || time.abrev}</div>

// ✅ IDEAL
<div className="font-semibold text-sm text-primary hover:text-primary/80 underline decoration-dotted cursor-pointer transition-colors">
  {time.nome || time.abrev}
</div>
```

**+ Adicionar tooltip:**
```tsx
<Tooltip>
  <TooltipTrigger asChild>
    <Link to={...}>
      {/* conteúdo */}
    </Link>
  </TooltipTrigger>
  <TooltipContent>
    <p>Ver análise detalhada, probabilidades e próximos jogos</p>
  </TooltipContent>
</Tooltip>
```

---

### 2. **Falta de Tooltips/Explicações** (PRIORIDADE ALTA)

#### `/brasileirao` (Classificação + Simulação)
- ❌ Sem legenda das cores (G-4 Libertadores, G-6 Pré-Libertadores, G-12 Sulamericana, Z-4 Rebaixamento)
- ❌ Sem explicação "Monte Carlo" (usuário leigo não sabe o que é)
- ❌ Sem tooltip nos ícones (Trophy, TrendingUp, Shield, Target, BarChart3)
- ❌ Sem explicação do badge "🔴 AO VIVO"
- ❌ Siglas "V/E/D" sem tooltip (Vitória/Empate/Derrota na forma)
- ❌ "SG" sem tooltip (Saldo de Gols)
- ❌ Percentuais sem contexto (ex: 33.8% de quê?)

#### `/dashboard` (Home)
- ❌ Sem explicação "MPV" (Maior Pontuação Valorizada)
- ❌ Sem tooltip em "Patrimônio"
- ❌ Sem explicação "4-4-2" para leigos
- ❌ "xG" sem tooltip (Expected Goals)
- ❌ Status "provável/dúvida/contundido" sem legendas

#### `/brasileirao/time/:slug` (TimePage)
- ❌ Sem explicação "Monte Carlo" na seção de probabilidades
- ❌ "xG" sem tooltip
- ❌ Força Casa/Fora/Geral sem explicação da escala (0-100?)
- ❌ "Placar Provável" sem contexto (baseado em quê?)
- ❌ Aproveitamento sem explicação (pontos conquistados / pontos disputados)

#### `/brasileirao/jogo/:id` (JogoPage)
- ❌ "1X2" sem explicação (casa/empate/fora)
- ❌ "Over/Under" sem explicação (mais/menos de X gols)
- ❌ "xG" repetido sem tooltip
- ❌ Probabilidades sem contexto

#### `/escalacao` (Seleção de Time)
- ❌ Filtros sem help text
- ❌ "Scout" sem explicação
- ❌ Status dos jogadores sem legenda
- ❌ Valorização sem contexto temporal (últimas X rodadas?)

#### `/mercado` (Análise de Mercado)
- ❌ Sem explicação dos critérios de ordenação
- ❌ Sem tooltip em "Variação (%)"

#### `/estatisticas` (Aba Defesa/Ataque/xG)
- ❌ "xG" repetido múltiplas vezes sem explicação
- ❌ "NPxG" sem explicação (Non-Penalty xG)
- ❌ Métricas defensivas sem contexto

#### `/confrontos` (Análise H2H)
- ❌ Sem explicação "Histórico últimos X jogos"
- ❌ Sem tooltip em "Aproveitamento"

---

### 3. **Falta de Legendas/Help Sections** (PRIORIDADE MÉDIA)

#### Páginas que precisam de seção "Como interpretar"
- [ ] `/brasileirao` → Explicar faixas de classificação (cores)
- [ ] `/brasileirao/time/:slug` → Explicar Monte Carlo, xG, forças
- [ ] `/brasileirao/jogo/:id` → Explicar 1X2, Over/Under, xG
- [ ] `/dashboard` → Explicar MPV, patrimônio
- [ ] `/estatisticas` → Glossário de métricas (xG, NPxG, etc)

---

### 4. **Ícones sem Contexto** (PRIORIDADE MÉDIA)

#### Ícones usados sem label/tooltip:
```tsx
// Brasileirao.tsx
<Trophy /> // Sem tooltip "Título"
<TrendingUp /> // Sem tooltip "Libertadores"
<TrendingDown /> // Sem tooltip "Rebaixamento"
<Target /> // Sem tooltip "Sulamericana"
<BarChart3 /> // Sem tooltip "Estatísticas"
<Shield /> // Sem tooltip "Defesa"

// Dashboard.tsx
<Users /> // Sem tooltip "Jogadores"
<Wallet /> // Sem tooltip "Patrimônio"
<Zap /> // Sem tooltip "Atualização automática"
<Clock /> // Sem tooltip "Tempo até fechamento"

// TimePage.tsx
<Info /> // Generic, precisa de contexto específico
```

---

### 5. **Affordances Visuais Fracas** (PRIORIDADE MÉDIA)

#### Elementos interativos sem indicadores claros:
- [ ] Tabs (Classificação/Simulação) - sem cursor pointer
- [ ] Cards expansíveis - sem indicador de expansão
- [ ] Botões "Ver mais" - sem hover state forte
- [ ] Filtros ativos - sem destaque visual

---

## ✅ Plano de Implementação

### Fase 1: Correções Críticas (Hoje)
1. ✅ **Tornar links da tabela obviamente clicáveis**
   - Adicionar cor primary
   - Adicionar underline dotted
   - Adicionar tooltip explicativo
   - Adicionar cursor pointer mais visível

2. ✅ **Adicionar tooltips em TODOS os ícones**
   - Instalar @radix-ui/react-tooltip (se não estiver)
   - Criar componente <IconWithTooltip>
   - Substituir ícones standalone

3. ✅ **Adicionar legenda de cores na tabela**
   - Seção explicativa abaixo do cabeçalho
   - Cores das faixas (G-4, G-6, G-12, Z-4)

### Fase 2: Tooltips Essenciais (Hoje)
1. ✅ **Glossário de termos técnicos**
   - MPV, xG, Monte Carlo, 1X2, Over/Under
   - Criar componente <TermTooltip term="xG">

2. ✅ **Explicações inline**
   - Percentuais (ex: "33.8% de título")
   - Métricas (ex: "Força: 95.7/100")
   - Status (ex: "Provável ✅", "Dúvida ⚠️")

### Fase 3: Help Sections (Próxima)
1. [ ] **Seção "Como interpretar" em cada página**
   - Accordion expansível
   - Texto simples, sem jargão
   - Exemplos práticos

2. [ ] **Tour guiado no primeiro acesso**
   - Intro.js ou Shepherd.js
   - 5-7 steps explicando features principais

### Fase 4: Refinamentos (Opcional)
1. [ ] **Vídeos/GIFs explicativos**
2. [ ] **FAQ contextual**
3. [ ] **Chatbot de ajuda**
4. [ ] **Feedback form em cada página**

---

## 🎨 Componentes Necessários

### 1. `<IconWithTooltip>`
```tsx
interface IconWithTooltipProps {
  icon: React.ReactNode;
  tooltip: string;
  className?: string;
}

export function IconWithTooltip({ icon, tooltip, className }: IconWithTooltipProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className={cn("inline-flex", className)}>
          {icon}
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <p>{tooltip}</p>
      </TooltipContent>
    </Tooltip>
  );
}
```

### 2. `<TermTooltip>`
```tsx
interface TermTooltipProps {
  term: 'xg' | 'mpv' | 'monte-carlo' | '1x2' | 'over-under';
  children: React.ReactNode;
}

const TERM_DEFINITIONS = {
  'xg': 'Expected Goals (xG): Métrica que estima a qualidade das chances criadas, baseada em dados estatísticos de milhares de jogos.',
  'mpv': 'Maior Pontuação Valorizada: Jogadores que mais pontuam considerando o custo-benefício (pontos ÷ preço).',
  'monte-carlo': 'Simulação Monte Carlo: Algoritmo que simula o campeonato 1000 vezes para calcular probabilidades realistas.',
  '1x2': 'Aposta 1X2: Probabilidade de vitória do mandante (1), empate (X) ou vitória do visitante (2).',
  'over-under': 'Over/Under: Probabilidade de o jogo ter mais (Over) ou menos (Under) que determinado número de gols.'
};

export function TermTooltip({ term, children }: TermTooltipProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="border-b border-dotted border-muted-foreground cursor-help">
          {children}
        </span>
      </TooltipTrigger>
      <TooltipContent className="max-w-xs">
        <p className="text-sm">{TERM_DEFINITIONS[term]}</p>
      </TooltipContent>
    </Tooltip>
  );
}
```

### 3. `<HelpSection>`
```tsx
interface HelpSectionProps {
  title: string;
  items: { term: string; definition: string }[];
}

export function HelpSection({ title, items }: HelpSectionProps) {
  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="help">
        <AccordionTrigger className="text-sm">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4" />
            {title}
          </div>
        </AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3 text-sm">
            {items.map((item) => (
              <div key={item.term} className="space-y-1">
                <dt className="font-semibold text-foreground">{item.term}</dt>
                <dd className="text-muted-foreground">{item.definition}</dd>
              </div>
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
```

### 4. `<ColorLegend>`
```tsx
export function ColorLegend() {
  return (
    <div className="bg-muted/30 p-4 rounded-lg space-y-2">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <Info className="w-4 h-4" />
        Legenda das Faixas de Classificação
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-primary/20 border-2 border-primary" />
          <span><strong>G-4:</strong> Libertadores (direto)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-info/20 border-2 border-info" />
          <span><strong>G-6:</strong> Libertadores (pré)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-warning/20 border-2 border-warning" />
          <span><strong>G-12:</strong> Sulamericana</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-destructive/20 border-2 border-destructive" />
          <span><strong>Z-4:</strong> Rebaixamento</span>
        </div>
      </div>
    </div>
  );
}
```

---

## 📦 Dependências Necessárias

```bash
# Já instaladas
✅ @radix-ui/react-tooltip (via shadcn/ui)
✅ @radix-ui/react-accordion (via shadcn/ui)
✅ lucide-react

# Opcionais para Fase 3+4
[ ] react-joyride (tour guiado)
[ ] intro.js (alternativa para tour)
```

---

## 🧪 Checklist de Teste (Pós-Implementação)

### Testes de Usabilidade
- [ ] Usuário leigo identifica links clicáveis sem ajuda
- [ ] Usuário leigo entende o que é "xG" após ler tooltip
- [ ] Usuário leigo identifica as faixas de classificação
- [ ] Usuário leigo entende o que é "Monte Carlo"
- [ ] Usuário leigo consegue interpretar probabilidades
- [ ] Usuário leigo entende status dos jogadores

### Testes Técnicos
- [ ] Tooltips aparecem em hover (desktop)
- [ ] Tooltips aparecem em click/touch (mobile)
- [ ] Tooltips não quebram layout em telas pequenas
- [ ] Cores de links têm contraste WCAG AA (4.5:1)
- [ ] Cursor pointer aparece em todos os elementos clicáveis
- [ ] Performance não afetada (adicionar tooltips lazy)

---

## 🎯 Métricas de Sucesso

1. **Taxa de cliques em times da tabela:** +300% esperado
2. **Tempo médio na página:** +50% (mais engajamento)
3. **Taxa de rejeição:** -30% (menos confusão)
4. **Help requests:** -80% (menos suporte necessário)

---

## 📝 Notas de Implementação

- **TooltipProvider:** Adicionar no App.tsx uma única vez (não em cada componente)
- **Mobile-first:** Tooltips devem funcionar em touch (click para abrir, click fora para fechar)
- **Acessibilidade:** Usar `aria-label` em todos os ícones, mesmo com tooltip
- **Performance:** Lazy load HelpSection (não bloquear render inicial)
- **i18n:** Preparar para internacionalização futura (PT-BR → EN)

---

**Próximo passo:** Implementar Fase 1 (correções críticas) ⚡
