# 🚀 Opções de SEO para ScoutDados

## Status Atual
- ✅ SPA React + Vite funcionando
- ✅ Meta tags dinâmicas (react-helmet-async)
- ❌ HTML inicial genérico para todas rotas
- ❌ Preview social sempre mostra home

## Problema Confirmado
```bash
curl https://scoutdados.com.br/brasileirao/jogo/vitoria-ba-x-flamengo-rj
# Retorna index.html genérico com meta tags da home
```

---

## Soluções (da mais simples à mais complexa)

### 🥇 Opção A: Pré-render com vite-plugin-ssr (SSG)
**Tempo estimado:** 2-4h  
**Impacto SEO:** 🟢🟢🟢🟢 90%  
**Complexidade:** Baixa  
**Mantém stack atual:** ✅ Sim (continua Vite + React)

#### Como funciona:
1. No `npm run build`, o Vite gera HTML "de verdade" para cada rota do seu sitemap
2. Exemplo: `/brasileirao/jogo/vitoria-ba-x-flamengo-rj/index.html` já vem com:
   - `<title>Vitória 1x2 Flamengo - Previsão | ScoutDados</title>`
   - Meta tags OG corretas
   - Dados iniciais da API embutidos no HTML (hidratação instantânea)
3. Continua sendo SPA após carregamento (navegação instant sem reload)

#### Instalação:
```bash
cd frontend
bun add -D vite-plugin-ssr vite-plugin-prerender
```

#### Configuração (vite.config.ts):
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { VitePluginSSR } from 'vite-plugin-ssr/plugin'

export default defineConfig({
  plugins: [
    react(),
    VitePluginSSR({
      // Rotas que serão pré-renderizadas
      routes: [
        '/',
        '/brasileirao',
        '/confrontos',
        '/dashboard',
        '/escalacao',
        '/mercado',
        '/scouts',
        '/estatisticas',
        '/blog',
        // Rotas dinâmicas (precisa de script para gerar lista)
        ...gerarRotasDeTimes(), // Função que lê do banco/API
        ...gerarRotasDeJogos(),
        ...gerarRotasDeBlog(),
      ]
    })
  ]
})
```

#### Trade-offs:
**Prós:**
- ✅ HTML perfeito para Googlebot/bots sociais
- ✅ Mantém Vite + React
- ✅ Build time aumenta pouco (~30s mais)
- ✅ Não precisa reescrever código
- ✅ Deploy continua igual (frontend/dist/)

**Contras:**
- ⚠️ Build precisa acessar API do backend (localhost:8000) para gerar HTMLs
- ⚠️ Toda vez que roda build, precisa regenerar tudo (ou incrementa só o que mudou)
- ⚠️ Rotas novas (jogos novos) precisam de novo build para serem pré-renderizadas

---

### 🥈 Opção B: Middleware OpenLiteSpeed (Meta Tags On-The-Fly)
**Tempo estimado:** 3-5h  
**Impacto SEO:** 🟢🟢🟢 70%  
**Complexidade:** Média  
**Mantém stack atual:** ✅ Sim

#### Como funciona:
1. OpenLiteSpeed intercepta requests de `/brasileirao/jogo/*`
2. Consulta backend `/api/brasileirao/jogo/{id}` para pegar dados
3. Injeta meta tags corretas no `<head>` do index.html antes de enviar
4. Só funciona para bots (User-Agent detection), usuários normais recebem SPA

#### Implementação (OpenLiteSpeed Rewrite Rules):
```apache
# /usr/local/lsws/conf/vhosts/scoutdados/rewrite.conf
RewriteEngine On

# Se for bot (Googlebot, Twitterbot, WhatsApp, etc)
RewriteCond %{HTTP_USER_AGENT} (bot|crawler|spider|facebookexternalhit|WhatsApp|Telegram) [NC]
RewriteRule ^/brasileirao/jogo/(.*)$ /meta-injector.php?path=$1 [L]

# Caso contrário, serve SPA normal
RewriteRule ^/(.*)$ /index.html [L]
```

**meta-injector.php:**
```php
<?php
// Busca dados do backend
$path = $_GET['path'];
$apiUrl = "http://localhost:8000/api/brasileirao/jogo/$path";
$data = json_decode(file_get_contents($apiUrl), true);

// Lê index.html
$html = file_get_contents('/www/wwwroot/scoutdados.com.br/frontend/dist/index.html');

// Injeta meta tags
$title = "{$data['mandante']['nome']} {$data['previsao']['placar_previsto']} {$data['visitante']['nome']}";
$html = preg_replace(
  '/<title>.*<\/title>/',
  "<title>$title - Previsão | ScoutDados</title>",
  $html
);

echo $html;
?>
```

#### Trade-offs:
**Prós:**
- ✅ Funciona imediatamente (não precisa rebuild)
- ✅ Rotas novas aparecem automaticamente
- ✅ Mantém SPA para usuários normais

**Contras:**
- ⚠️ Adiciona 50-200ms de latência para bots (request extra ao backend)
- ⚠️ Mais complexo de debugar
- ❌ Não resolve hydration (dados não vêm embutidos)
- ⚠️ PHP/logic no servidor web (mais pontos de falha)

---

### 🥉 Opção C: Migrar para Next.js (SSR + ISR)
**Tempo estimado:** 40-80h (reescrita completa)  
**Impacto SEO:** 🟢🟢🟢🟢🟢 100%  
**Complexidade:** Alta  
**Mantém stack atual:** ❌ Não (React fica, mas infraestrutura muda)

#### Como funciona:
- Next.js 14 com App Router
- SSR para páginas dinâmicas (jogos, times)
- ISR (Incremental Static Regeneration) para blog
- API Routes integradas (pode substituir FastAPI parcialmente)

#### Trade-offs:
**Prós:**
- ✅✅ SEO perfeito (HTML gerado no servidor por request)
- ✅ ISR = cache inteligente (gera HTML 1x, serve N vezes)
- ✅ Suporte oficial/comunidade gigante
- ✅ Image optimization, React Server Components

**Contras:**
- ❌❌ Reescrita completa do frontend (40-80h)
- ❌ Deploy muda (precisa de Node.js server rodando, não é mais "dist estático")
- ❌ OpenLiteSpeed serve Next, ou precisa PM2/Node em outra porta
- ⚠️ Bundle maior (Next.js adiciona overhead)

---

## 🎯 Recomendação Final

### Se você quer **SEO forte hoje + menos esforço**:
👉 **Opção A (vite-plugin-ssr)** - 2-4h de trabalho, 90% do resultado.

**Implementação básica:**
1. Instalar plugin: `bun add -D vite-plugin-ssr`
2. Criar script Python que lista todas rotas dinâmicas:
   ```python
   # generate_routes.py
   from api_server import CartolaAPI, get_db
   api = CartolaAPI()
   db = next(get_db())
   
   # Gera lista de jogos, times, posts
   jogos = db.query(...).all()
   times = api.get_clubes().values()
   posts = db.query(...).all()
   
   routes = [
       '/brasileirao',
       *[f'/brasileirao/jogo/{jogo.slug}' for jogo in jogos],
       *[f'/brasileirao/time/{time.slug}' for time in times],
       *[f'/blog/{post.slug}' for post in posts],
   ]
   print('\n'.join(routes))
   ```
3. Modificar `deploy.sh` para rodar esse script antes do build
4. Plugin gera HTML "de verdade" para cada rota

**Resultado:**
- Googlebot vê HTML completo → indexa rápido
- WhatsApp/Twitter/Discord preview funciona
- Usuários continuam com SPA rápida
- Deploy continua com `./deploy.sh`

---

### Se você quer **zero mudança por agora**:
👉 Deixar como está. 

**Por quê?**
- Googlebot **consegue** indexar seu site (só é mais lento/frágil)
- AdSense funciona normal (roda no navegador)
- Você não está competindo diretamente com portais de notícia (seu nicho é Cartola Fantasy, não apostas esportivas)
- O principal tráfego vem de busca "escalação cartola", "valorização cartola" → menos competição

**Faz sentido adiar SEO hardcore se:**
- Seu app já está funcionando e gerando valor
- Tráfego orgânico **já está crescendo** (verifica Google Analytics)
- Você tem outras prioridades (features novas, estabilidade, monetização)

---

## 📊 Métricas para Decidir

Antes de investir em SEO avançado, verifique:

```bash
# 1. Seu site está indexado?
site:scoutdados.com.br

# 2. Páginas profundas foram indexadas?
site:scoutdados.com.br/brasileirao/jogo

# 3. Quantas páginas o Google indexou?
# Se for <50 páginas → problema de indexação (precisa SSG)
# Se for >200 páginas → Googlebot está renderizando JS bem
```

**Google Search Console:**
- Páginas indexadas: quantas?
- Coverage errors: tem páginas descobertas mas não indexadas?
- Core Web Vitals: passando?

**Se você já tem 500+ páginas indexadas e aparecem nas buscas → SEO está OK, não precisa SSG com urgência.**

---

## 🔗 Links Úteis
- [vite-plugin-ssr docs](https://vite-plugin-ssr.com/)
- [Google: JavaScript SEO Guide](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- [Next.js ISR](https://nextjs.org/docs/pages/building-your-application/data-fetching/incremental-static-regeneration)

