# 🚀 Estratégia de Pre-render SSG — ScoutDados

## 🎯 Objetivo
Pré-renderizar apenas páginas que:
1. **Mudam raramente** (blog, páginas estáticas)
2. **Precisam de SEO forte** (compartilhamento social)
3. **Não quebram com dados levemente desatualizados** (times, scouts)

---

## ✅ Páginas Pré-renderizadas (30 páginas)

| Página | Por Que | Frequência de Rebuild |
|--------|---------|----------------------|
| `/` | Home - SEO crítico | Deploy |
| `/brasileirao` | Classificação - SEO | 1x por rodada |
| `/escalacao` | Formulário - não depende de dados atuais | Deploy |
| `/scouts` | Destaques da última rodada | 1x por rodada |
| `/blog` | Listagem | Quando publicar |
| `/blog/*` (6 posts) | Artigos - SEO crítico | Quando editar |
| `/sobre`, `/termos`, `/privacidade` | Estáticas | Deploy |
| `/brasileirao/time/*` (20 times) | Análise por time | 1x por rodada |

**Total:** ~30 páginas

---

## ❌ Páginas NÃO Pré-renderizadas (SPA puro)

| Página | Por Que | Como Funciona |
|--------|---------|--------------|
| `/dashboard` | Dados mudam constantemente | React Query fetch ao vivo |
| `/mercado` | Lista 200+ atletas em tempo real | React Query + filtros |
| `/confrontos` | Probabilidades/xG atualizados | Fetch dinâmico |
| `/historico` | **Causa erro React #310** | SPA (sem pre-render) |
| `/estatisticas` | Gráficos dinâmicos | SPA (sem pre-render) |

**Essas páginas continuam funcionando normalmente como SPA.**  
OLS serve `index.html` genérico → React Router carrega → React Query busca dados.

---

## ⏰ Quando Rodar o Pre-render?

### **Opção 1: Manual (recomendado por enquanto)**
```bash
# Quando publicar novo post no blog
cd /www/wwwroot/scoutdados.com.br
./deploy.sh  # Já inclui pre-render

# Quando começar nova rodada (atualizar times)
./deploy.sh --frontend-only
```

### **Opção 2: Cron semanal (automático)**
```bash
# Todo domingo 23h (fim de rodada)
0 23 * * 0 cd /www/wwwroot/scoutdados.com.br && ./deploy.sh --frontend-only > /tmp/prerender.log 2>&1
```

### **Opção 3: Trigger por mudança de rodada**
```python
# scheduler_service.py (atualizar no futuro)
def ao_trocar_rodada():
    subprocess.run(['bash', '/www/wwwroot/scoutdados.com.br/deploy.sh', '--frontend-only'])
```

---

## 🐛 Problemas Conhecidos & Soluções

### **Erro React #310 (Too many re-renders)**

**Causa:** Páginas com `useMemo` complexo + dependências que mudam causam loop.

**Páginas afetadas:**
- `/historico` — desabilitado pre-render ✅
- `/estatisticas` — desabilitado pre-render ✅

**Solução:**
- Essas páginas continuam funcionando como SPA normal
- Pre-render desabilitado não afeta funcionalidade

### **Títulos genéricos em ~6 páginas**

**Causa:** React Query ainda não buscou dados quando Puppeteer capturou HTML.

**Páginas afetadas:**
- `/sobre` (algumas vezes)
- `/scouts` (timing race)

**Impacto:** Baixo (Google re-indexa eventualmente)

**Solução futura:** Aumentar `RENDER_WAIT_STATIC_MS` de 3s para 5s.

---

## 📊 Métricas de Sucesso

### **Antes do Pre-render (SPA puro):**
```bash
curl https://scoutdados.com.br/brasileirao/time/flamengo
# <title>ScoutDados - Brasileirão 2026, Previsões e Cartola</title>
# ❌ Título genérico (mesmo para todas páginas)
```

### **Depois do Pre-render (SSG):**
```bash
curl https://scoutdados.com.br/brasileirao/time/flamengo/
# <title>FLA - Brasileirão 2026 | ScoutDados</title>
# ✅ Título específico da página
```

**Validar:**
```bash
# Blog
curl -sL https://scoutdados.com.br/blog/monte-carlo-futebol/ | grep '<title>'

# Time
curl -sL https://scoutdados.com.br/brasileirao/time/palmeiras/ | grep '<title>'

# Post com JSON-LD
curl -sL https://scoutdados.com.br/blog/xg-expected-goals/ | grep -c 'application/ld+json'
# Deve retornar: 2
```

---

## 🎯 Conclusão: Vale a Pena?

### ✅ **SIM, vale a pena MANTER**

**Motivos:**
1. **SEO forte para blog** (conteúdo indexado corretamente)
2. **Preview social funciona** (WhatsApp/Twitter/Discord)
3. **Times com meta tags únicas** (melhor posicionamento)
4. **Custo baixo** (5min de build, 1x por rodada)

**Trade-offs aceitos:**
- Dados dos times ficam "1 rodada desatualizados" no HTML estático
  - ✅ **Não importa:** Ao carregar no navegador, React Query busca dados frescos
  - ✅ **Crawlers veem snapshot razoável** (melhor que HTML genérico)

---

## 🚧 Futuro (se tráfego justificar)

Se o site crescer e pre-render virar gargalo, considerar:

1. **Incremental Static Regeneration (ISR)**  
   → Rebuild automático por página quando acessada  
   → Requer Next.js ou framework com ISR

2. **Edge SSR com cache**  
   → Cloudflare Workers renderiza HTML sob demanda  
   → Cache de 1h por página

3. **Separate CMS para blog**  
   → Headless CMS (Strapi, Ghost) com webhook  
   → Rebuild automático ao publicar post

**Por agora:** Pre-render manual/semanal é **suficiente e estável**. ✅

---

## 📝 Checklist de Deploy com Pre-render

```bash
# 1. Backend rodando?
curl -sf http://localhost:8000/api/status || echo "Backend offline"

# 2. Build frontend
cd /www/wwwroot/scoutdados.com.br/frontend
bun run build

# 3. Pre-render (vai pular páginas com erro)
node prerender.mjs
# Aguarde: ~5min para 30 páginas

# 4. Conferir
ls -lh dist/brasileirao/time/flamengo/index.html
# Deve ter ~60KB (com dados da API)

# 5. Restart OLS
sudo /usr/local/lsws/bin/lswsctrl restart

# 6. Validar ao vivo
curl -sL https://scoutdados.com.br/brasileirao/time/flamengo/ | grep '<title>'
```

---

## 🔗 Arquivos Relacionados

- `frontend/prerender.mjs` — Script de pre-render
- `deploy.sh` — Deploy automático (linha 85+)
- `docs/OPCOES_SEO.md` — Análise das opções de SEO
- `frontend/src/components/SEO.tsx` — Componente de meta tags

---

**Última atualização:** 07/02/2026  
**Status:** ✅ Em produção (30 páginas pré-renderizadas)
