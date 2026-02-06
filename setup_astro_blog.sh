#!/bin/bash
set -e

echo "🚀 Setup Astro Blog - SSG para SEO"
echo "=================================="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Diretórios
PROJECT_ROOT="/root/cartolafc2026"
BLOG_DIR="$PROJECT_ROOT/blog"

cd "$PROJECT_ROOT"

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js não encontrado. Instalando...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

NODE_VERSION=$(node -v)
echo -e "${GREEN}✅ Node.js: $NODE_VERSION${NC}"

# Criar projeto Astro
if [ -d "$BLOG_DIR" ]; then
    echo -e "${YELLOW}⚠️  Diretório blog/ já existe. Removendo...${NC}"
    rm -rf "$BLOG_DIR"
fi

echo ""
echo "📦 Criando projeto Astro..."
npm create astro@latest blog -- --template minimal --no-install --no-git --typescript strict

cd "$BLOG_DIR"

# Instalar dependências
echo ""
echo "📦 Instalando dependências..."
npm install

# Adicionar dependências extras
npm install -D @astrojs/mdx @astrojs/sitemap @astrojs/tailwind tailwindcss

# Configurar Astro
echo ""
echo "⚙️  Configurando Astro..."

cat > astro.config.mjs << 'ASTRO_CONFIG'
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://scoutdados.com.br',
  base: '/',
  output: 'static',
  integrations: [
    mdx(),
    sitemap(),
    tailwind()
  ],
  build: {
    assets: '_astro'
  },
  vite: {
    build: {
      rollupOptions: {
        output: {
          assetFileNames: '_astro/[name].[hash][extname]'
        }
      }
    }
  }
});
ASTRO_CONFIG

# Configurar Tailwind
npx tailwindcss init

cat > tailwind.config.mjs << 'TAILWIND_CONFIG'
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        primary: '#10b981',
        secondary: '#3b82f6',
      }
    },
  },
  plugins: [],
}
TAILWIND_CONFIG

# Criar estrutura de diretórios
mkdir -p src/{layouts,pages,components,content/posts,styles}

# Layout base
cat > src/layouts/BaseLayout.astro << 'LAYOUT'
---
interface Props {
  title: string;
  description?: string;
}

const { title, description = "Scout, análise e estatísticas de futebol para Cartola FC" } = Astro.props;
const canonicalURL = new URL(Astro.url.pathname, Astro.site);
---

<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="canonical" href={canonicalURL} />
    
    <title>{title}</title>
    <meta name="description" content={description} />
    
    <!-- Open Graph -->
    <meta property="og:type" content="website" />
    <meta property="og:url" content={canonicalURL} />
    <meta property="og:title" content={title} />
    <meta property="og:description" content={description} />
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content={title} />
    <meta name="twitter:description" content={description} />
  </head>
  <body class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <div class="flex items-center">
            <a href="/" class="text-2xl font-bold text-primary">ScoutDados</a>
          </div>
          <div class="flex space-x-6">
            <a href="/" class="text-gray-700 hover:text-primary">Início</a>
            <a href="/blog" class="text-gray-700 hover:text-primary">Blog</a>
            <a href="/tools" class="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90">Ferramentas</a>
          </div>
        </div>
      </div>
    </nav>
    
    <main>
      <slot />
    </main>
    
    <footer class="bg-gray-900 text-white mt-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 class="text-lg font-bold mb-4">ScoutDados</h3>
            <p class="text-gray-400">Análise inteligente de futebol com dados e estatísticas para Cartola FC.</p>
          </div>
          <div>
            <h3 class="text-lg font-bold mb-4">Links</h3>
            <ul class="space-y-2 text-gray-400">
              <li><a href="/" class="hover:text-white">Início</a></li>
              <li><a href="/blog" class="hover:text-white">Blog</a></li>
              <li><a href="/tools" class="hover:text-white">Ferramentas</a></li>
            </ul>
          </div>
          <div>
            <h3 class="text-lg font-bold mb-4">Legal</h3>
            <ul class="space-y-2 text-gray-400">
              <li><a href="/privacidade" class="hover:text-white">Privacidade</a></li>
              <li><a href="/termos" class="hover:text-white">Termos de Uso</a></li>
            </ul>
          </div>
        </div>
        <div class="mt-8 pt-8 border-t border-gray-800 text-center text-gray-400">
          <p>&copy; 2026 ScoutDados. Todos os direitos reservados.</p>
        </div>
      </div>
    </footer>
  </body>
</html>
LAYOUT

# CSS Global
cat > src/styles/global.css << 'CSS'
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply antialiased;
  }
}
CSS

# Página inicial
cat > src/pages/index.astro << 'INDEX'
---
import BaseLayout from '../layouts/BaseLayout.astro';
---

<BaseLayout title="ScoutDados - Análise e Estatísticas de Futebol para Cartola FC">
  <div class="bg-gradient-to-br from-primary/10 to-secondary/10 py-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <h1 class="text-5xl font-bold text-gray-900 mb-6">
        Análise Inteligente para o Cartola FC
      </h1>
      <p class="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
        Dados, estatísticas e algoritmos de machine learning para escalar o melhor time e valorizar seu patrimônio.
      </p>
      <div class="flex gap-4 justify-center">
        <a href="/tools" class="bg-primary text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary/90 transition">
          Acessar Ferramentas
        </a>
        <a href="/blog" class="bg-white text-primary px-8 py-4 rounded-lg text-lg font-semibold border-2 border-primary hover:bg-primary/5 transition">
          Ler Blog
        </a>
      </div>
    </div>
  </div>

  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
    <h2 class="text-3xl font-bold text-center mb-12">Principais Recursos</h2>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div class="bg-white p-6 rounded-lg shadow-md">
        <div class="text-4xl mb-4">📊</div>
        <h3 class="text-xl font-bold mb-2">Análise de Confrontos</h3>
        <p class="text-gray-600">Algoritmo que analisa força ofensiva/defensiva, mando de campo e forma recente dos times.</p>
      </div>
      
      <div class="bg-white p-6 rounded-lg shadow-md">
        <div class="text-4xl mb-4">💰</div>
        <h3 class="text-xl font-bold mb-2">Valorização Inteligente</h3>
        <p class="text-gray-600">Identifica jogadores com alto potencial de valorização usando histórico e tendências.</p>
      </div>
      
      <div class="bg-white p-6 rounded-lg shadow-md">
        <div class="text-4xl mb-4">⚡</div>
        <h3 class="text-xl font-bold mb-2">Escalação Automática</h3>
        <p class="text-gray-600">Gera times otimizados considerando orçamento, formação e análise de confrontos.</p>
      </div>
    </div>
  </div>

  <div class="bg-gray-100 py-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <h2 class="text-3xl font-bold mb-4">Pronto para começar?</h2>
      <p class="text-xl text-gray-600 mb-8">
        Acesse as ferramentas gratuitamente. Sem cadastro, sem limite.
      </p>
      <a href="/tools" class="bg-primary text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-primary/90 transition inline-block">
        Começar Agora →
      </a>
    </div>
  </div>
</BaseLayout>

<style>
  @import '../styles/global.css';
</style>
INDEX

# Página de blog
cat > src/pages/blog/index.astro << 'BLOG_INDEX'
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';

const posts = await getCollection('posts');
const sortedPosts = posts.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());
---

<BaseLayout title="Blog - ScoutDados" description="Artigos sobre estratégias, análises e dicas para o Cartola FC">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-4xl font-bold mb-2">Blog</h1>
    <p class="text-xl text-gray-600 mb-12">Estratégias, análises e dicas para dominar o Cartola FC</p>
    
    <div class="space-y-8">
      {sortedPosts.map((post) => (
        <article class="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition">
          <a href={`/blog/${post.slug}`} class="block">
            <h2 class="text-2xl font-bold text-gray-900 mb-2 hover:text-primary">
              {post.data.title}
            </h2>
            <p class="text-gray-600 mb-4">{post.data.description}</p>
            <div class="flex items-center text-sm text-gray-500">
              <time datetime={post.data.date.toISOString()}>
                {post.data.date.toLocaleDateString('pt-BR', { 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </time>
              <span class="mx-2">•</span>
              <span>{post.data.author}</span>
            </div>
          </a>
        </article>
      ))}
    </div>
  </div>
</BaseLayout>

<style>
  @import '../../styles/global.css';
</style>
BLOG_INDEX

# Template de post individual
cat > src/pages/blog/[...slug].astro << 'BLOG_POST'
---
import BaseLayout from '../../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const posts = await getCollection('posts');
  return posts.map((post) => ({
    params: { slug: post.slug },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await post.render();
---

<BaseLayout title={post.data.title} description={post.data.description}>
  <article class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <header class="mb-8">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">{post.data.title}</h1>
      <div class="flex items-center text-gray-600">
        <time datetime={post.data.date.toISOString()}>
          {post.data.date.toLocaleDateString('pt-BR', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </time>
        <span class="mx-2">•</span>
        <span>{post.data.author}</span>
      </div>
    </header>
    
    <div class="prose prose-lg max-w-none">
      <Content />
    </div>
    
    <div class="mt-12 pt-8 border-t">
      <a href="/blog" class="text-primary hover:underline">← Voltar para o blog</a>
    </div>
  </article>
</BaseLayout>

<style>
  @import '../../styles/global.css';
  
  .prose {
    @apply text-gray-800;
  }
  
  .prose :global(h2) {
    @apply text-2xl font-bold mt-8 mb-4;
  }
  
  .prose :global(h3) {
    @apply text-xl font-bold mt-6 mb-3;
  }
  
  .prose :global(p) {
    @apply mb-4 leading-relaxed;
  }
  
  .prose :global(ul), .prose :global(ol) {
    @apply mb-4 ml-6;
  }
  
  .prose :global(li) {
    @apply mb-2;
  }
  
  .prose :global(strong) {
    @apply font-bold text-gray-900;
  }
  
  .prose :global(a) {
    @apply text-primary hover:underline;
  }
  
  .prose :global(code) {
    @apply bg-gray-100 px-2 py-1 rounded text-sm;
  }
</style>
BLOG_POST

# Configurar coleção de posts
cat > src/content/config.ts << 'CONFIG_TS'
import { defineCollection, z } from 'astro:content';

const postsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.date(),
    author: z.string().default('Equipe ScoutDados'),
    tags: z.array(z.string()).optional(),
  }),
});

export const collections = {
  posts: postsCollection,
};
CONFIG_TS

# Criar posts de exemplo
mkdir -p src/content/posts

cat > src/content/posts/como-funciona-mpv-cartola-fc.md << 'POST1'
---
title: "Como Funciona o Algoritmo de MPV (Média de Pontos por Valor)"
description: "Entenda como calculamos a eficiência de cada jogador no Cartola FC usando a métrica MPV e como ela te ajuda a escalar melhor."
date: 2026-02-01
author: "Equipe ScoutDados"
tags: ["cartola", "algoritmo", "mpv", "estrategia"]
---

# Como Funciona o Algoritmo de MPV (Média de Pontos por Valor)

O **MPV (Média de Pontos por Valor)** é uma das métricas mais importantes para identificar jogadores eficientes no Cartola FC. Mas como ela realmente funciona?

## O Que É MPV?

MPV mede quantos pontos um jogador entrega **por cartoleta investida**. É calculado assim:

```
MPV = Média de Pontos / Preço do Jogador
```

Por exemplo:
- **Jogador A**: 8 pontos de média, C$ 10 → MPV = 0.80
- **Jogador B**: 6 pontos de média, C$ 5 → MPV = 1.20

O Jogador B tem **melhor MPV** mesmo pontuando menos!

## Por Que MPV Importa?

No Cartola, você tem **orçamento limitado** (100 cartoletas). Jogadores com alto MPV permitem:

✅ Montar times competitivos gastando menos  
✅ Sobrar dinheiro para investir em outras posições  
✅ Maximizar pontos totais do time

## Como Usamos MPV no ScoutDados

Nosso algoritmo não usa apenas MPV isolado. Combinamos:

1. **MPV base** - Eficiência histórica
2. **Tendência** - Jogador está melhorando ou piorando?
3. **Confronto** - Adversário facilita ou dificulta?
4. **Risco** - Chance de lesão/suspensão

## Exemplo Prático

Na rodada 1 de 2026, nosso algoritmo identificou:

- **Gabriel Menino** (C$ 6.00, MPV 1.05) → Valorizou 79.5%
- **Léo Pereira** (C$ 8.50, MPV 0.85) → Valorizou 12.4%

O segredo? Combinar MPV com análise de confronto!

## Conclusão

MPV é poderoso, mas **não é tudo**. Use junto com outras análises para escalar times vencedores.

**Quer testar?** Acesse nossas [ferramentas de escalação](/tools) gratuitamente!
POST1

cat > src/content/posts/estrategia-valorizacao-cartola.md << 'POST2'
---
title: "Estratégia de Valorização: Como Aumentar Seu Patrimônio no Cartola"
description: "Descubra a faixa de preço ideal (C$ 3-6) e técnicas para valorizar jogadores e multiplicar seu patrimônio ao longo do campeonato."
date: 2026-02-02
author: "Equipe ScoutDados"
tags: ["cartola", "valorizacao", "patrimonio", "estrategia"]
---

# Estratégia de Valorização: Como Aumentar Seu Patrimônio

Muitos cartoleiros focam apenas em **pontos**. Mas e se eu te disser que você pode **multiplicar seu patrimônio** e DEPOIS montar times ainda melhores?

## O Sweet Spot: C$ 3 - C$ 6

Nossos dados de 2025 mostram que jogadores entre **C$ 3 e C$ 6** têm:

- ✅ **Maior potencial de valorização** (50-200%)
- ✅ **Menor risco** comparado a muito baratos
- ✅ **ROI superior** a jogadores caros

### Por Que Essa Faixa?

**Muito baratos (C$ 2-3):**
- Alta volatilidade
- Podem não jogar

**Faixa ideal (C$ 3-6):**
- Reservas virando titulares
- Jogadores em boa fase
- Preço ainda não reflete qualidade

**Muito caros (C$ 10+):**
- Pouco espaço para valorizar
- Alto custo de oportunidade

## Técnica: Time de Valorização

Todo sábado, monte **2 times**:

1. **Time Pontos** - Foca em pontuar na rodada
2. **Time Valorização** - Foca em C$ 3-6 com confrontos fáceis

## Exemplo Real: Rodada 1/2026

Escalamos o "Time Valorização" com:

| Jogador | Preço Inicial | Preço Final | Valorização |
|---------|---------------|-------------|-------------|
| Gabriel Menino | C$ 6.00 | C$ 10.77 | +79.5% |
| Léo Derik | C$ 2.00 | C$ 5.14 | +157% |
| Hulk | C$ 10.00 | C$ 12.40 | +24% |

**Resultado:** Patrimônio subiu de C$ 100 para C$ 128 em **1 rodada**!

## Como Identificar Jogadores C$ 3-6 com Potencial?

Use esses filtros no [ScoutDados](/tools):

1. **Preço:** C$ 3.00 - C$ 6.00
2. **Status:** Provável (não dúvida)
3. **Confronto:** Favorável (força ofensiva > defensiva adversário)
4. **Tendência:** Últimas 3 rodadas em alta

## Quando Vender?

**Regra de ouro:** Venda quando valorizar **+30% a +50%**

Não seja ganancioso. Reinvista em novos C$ 3-6!

## Conclusão

Valorização é **jogo de longo prazo**. Patrimônio hoje = times melhores depois.

**Comece agora:** Acesse as [ferramentas de análise](/tools)!
POST2

cat > src/content/posts/analise-confrontos-cartola.md << 'POST3'
---
title: "Análise de Confrontos: O Segredo para Escalar Melhor"
description: "Aprenda como analisar força ofensiva, defensiva e mando de campo para identificar jogadores que vão pontuar mais."
date: 2026-02-03
author: "Equipe ScoutDados"
tags: ["cartola", "confrontos", "mando", "scouts"]
---

# Análise de Confrontos: O Segredo para Escalar Melhor

A maioria dos cartoleiros escolhe jogadores apenas pela **média de pontos**. Mas e se o adversário dele for muito forte? Você vai tomar 0 pontos!

## Por Que Confrontos Importam?

Um atacante com 8 de média contra **defesa forte** pode fazer 2 pontos.  
O mesmo atacante contra **defesa fraca** pode fazer 15 pontos!

### Dados Reais

Analisamos 380 rodadas do Brasileirão e descobrimos:

- **Atacantes** jogando em casa contra defesas fracas: **+45% de pontos**
- **Defensores** jogando fora contra ataques fortes: **-35% de pontos**

## Como Analisar Um Confronto

### 1. Força Ofensiva vs Defensiva

Compare:

**Time A (Flamengo)**
- Gols marcados: 2.1/jogo (forte)

vs

**Time B (Cuiabá)**  
- Gols sofridos: 1.8/jogo (defesa fraca)

**Conclusão:** Atacantes do Flamengo têm confronto favorável!

### 2. Mando de Campo

Times jogando **em casa** marcam **30% mais gols** que fora.

Priorize:
- ✅ Atacantes do mandante
- ✅ Defensores/goleiros do visitante (se adversário fraco)

### 3. Forma Recente

Últimas **3 rodadas** importam mais que média histórica.

Time em alta = confiança = mais pontos

## Exemplo Prático: Palmeiras x Santos

**Confronto:** Palmeiras (casa) vs Santos (visitante)

**Análise:**
- Palmeiras: 12 gols últimas 3 rodadas (em alta)
- Santos: 7 gols sofridos últimas 3 rodadas (defesa ruim)
- Mando: Allianz Parque favorece Palmeiras

**Conclusão:** Atacantes do Palmeiras = OBRIGATÓRIOS

## Como Usar no ScoutDados

Nossa ferramenta de [análise de confrontos](/tools) calcula automaticamente:

1. ⚔️ Força ofensiva vs defensiva
2. 🏠 Vantagem de mando
3. 📈 Forma recente (3 rodadas)
4. 🎯 Chance de saldo de gol positivo

**Resultado:** Score de 0-100 para cada confronto!

## Dica Bônus: Evite "Confrontos Diretos"

Quando líder enfrenta vice, é um **clássico equilibrado**:
- Poucos gols
- Muito cartão
- Pontuação baixa para todos

**Fuja desses jogos!**

## Conclusão

Confronto é 40% da escalação. Média de pontos é só 30%.

**Use a ferramenta:** [Análise de Confrontos](/tools) gratuita!
POST3

# Criar favicon
cat > public/favicon.svg << 'FAVICON'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" fill="#10b981"/>
  <text x="50" y="75" font-size="60" font-weight="bold" text-anchor="middle" fill="white">S</text>
</svg>
FAVICON

echo ""
echo -e "${GREEN}✅ Astro blog criado com sucesso!${NC}"
echo ""
echo "📋 Estrutura criada:"
echo "  ├── src/pages/index.astro (landing)"
echo "  ├── src/pages/blog/index.astro (lista posts)"
echo "  ├── src/pages/blog/[...slug].astro (post individual)"
echo "  └── src/content/posts/ (3 posts exemplo)"
echo ""
echo "🧪 Testar localmente:"
echo "  cd $BLOG_DIR"
echo "  npm run dev"
echo ""
echo "🏗️  Build para produção:"
echo "  npm run build"
echo "  # Gera dist/ com HTML estático"
echo ""
echo -e "${GREEN}✅ Setup concluído!${NC}"
