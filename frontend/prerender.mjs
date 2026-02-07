#!/usr/bin/env node
/**
 * ScoutDados SSG Pre-render
 * 
 * Usa Puppeteer para renderizar cada rota do SPA e salvar o HTML completo.
 * Roda APÓS `vite build` e ANTES do restart do OLS.
 * 
 * O OLS serve arquivos estáticos antes do fallback SPA (RewriteCond !-f),
 * então os HTMLs pré-renderizados são servidos diretamente para crawlers.
 * 
 * Uso: node prerender.mjs
 * Env: CHROMIUM_PATH (default: /snap/bin/chromium)
 *       PRERENDER=false para desabilitar
 */
import { launch } from 'puppeteer';
import { createServer } from 'http';
import { createProxyMiddleware } from 'http-proxy-middleware';
import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join, resolve } from 'path';
import { mkdirSync, writeFileSync, existsSync, readdirSync, readFileSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ── Config ──
const DIST_DIR = join(__dirname, 'dist');
const CHROMIUM_PATH = process.env.CHROMIUM_PATH || '/snap/bin/chromium';
const API_TARGET = 'http://127.0.0.1:8000';
const CONCURRENCY = 2;
const CONCURRENCY_TEAM = 1;  // Teams hit slow sync API — render 1 at a time
const RENDER_WAIT_MS = 12000;  // Wait for React Query to fetch data
const RENDER_WAIT_STATIC_MS = 3000;  // Shorter wait for pages without API data
const DEFAULT_TITLE = 'ScoutDados - Brasileirão 2026, Previsões e Cartola';

// ── Routes ──
const STATIC_ROUTES = [
  '/',
  '/brasileirao',
  // '/confrontos',    // ❌ Dados mudam muito (desabilitado)
  // '/dashboard',     // ❌ Tempo real (desabilitado)
  '/escalacao',
  // '/mercado',       // ❌ Tempo real (desabilitado)
  '/scouts',
  // '/historico',     // ❌ Causa erro React #310 (desabilitado)
  // '/estatisticas',  // ❌ Dados dinâmicos (desabilitado)
  '/blog',
  '/sobre',
  '/privacidade',
  '/termos',
];

const TEAM_SLUGS = [
  'atletico-mg', 'athletico-pr', 'bahia', 'botafogo',
  'corinthians', 'cruzeiro', 'flamengo',
  'fluminense', 'gremio', 'internacional',
  'mirassol', 'palmeiras', 'santos',
  'sao-paulo', 'vasco', 'vitoria',
  'red-bull-bragantino', 'chapecoense', 'coritiba', 'remo',
];

const BLOG_SLUGS = [
  'monte-carlo-futebol',
  'xg-expected-goals',
  'classificacao-brasileirao-2026',
  'guia-cartola-fc-2026',
  'modelo-poisson-previsao-placares',
];

// Auto-discover blog posts from data/blog_posts/
function getAutoBlogSlugs() {
  const postsDir = join(__dirname, '..', 'data', 'blog_posts');
  if (!existsSync(postsDir)) return [];
  try {
    return readdirSync(postsDir)
      .filter(f => f.endsWith('.json'))
      .map(f => {
        try {
          const data = JSON.parse(readFileSync(join(postsDir, f), 'utf-8'));
          return data.slug || f.replace('.json', '');
        } catch { return f.replace('.json', ''); }
      });
  } catch { return []; }
}

// Pages that need API data (longer wait)
const API_ROUTES = new Set([
  '/brasileirao', '/confrontos', '/dashboard', '/escalacao',
  '/mercado', '/scouts', '/historico', '/estatisticas',
]);

function getWaitTime(route) {
  if (route.startsWith('/brasileirao/time/')) return RENDER_WAIT_MS;
  if (API_ROUTES.has(route)) return RENDER_WAIT_MS;
  return RENDER_WAIT_STATIC_MS;
}

// ── Express server with API proxy ──
function startServer() {
  return new Promise((resolve) => {
    const app = express();

    // Proxy /api/* → FastAPI backend
    app.use('/api', createProxyMiddleware({
      target: API_TARGET,
      changeOrigin: true,
      logLevel: 'warn',
    }));

    // Serve static files from dist/
    app.use(express.static(DIST_DIR));

    // SPA fallback: serve index.html for all other routes (Express 5 syntax)
    app.get('/{*splat}', (req, res) => {
      res.sendFile(join(DIST_DIR, 'index.html'));
    });

    const server = app.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      console.log(`  📦 Server listening on http://127.0.0.1:${port}`);
      resolve({ server, port });
    });
  });
}

// ── Render a single route ──
async function renderRoute(browser, baseUrl, route) {
  const page = await browser.newPage();
  const url = `${baseUrl}${route}`;
  const waitTime = getWaitTime(route);

  try {
    // Navigate and wait for network to settle
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

    // Smart wait strategy
    const isTeamPage = route.startsWith('/brasileirao/time/');
    const isApiPage = API_ROUTES.has(route);

    if (isTeamPage) {
      // Team pages: two-stage wait
      // Stage 1: Wait for React-Helmet to mount and set the default SEO title
      await page.waitForFunction(
        (defaultTitle) => document.title === defaultTitle,
        { timeout: 10000 },
        DEFAULT_TITLE
      ).catch(() => {});

      // Stage 2: Wait until title changes from default (= API data loaded, team-specific title set)
      try {
        await page.waitForFunction(
          (defaultTitle) => document.title !== defaultTitle,
          { timeout: 25000 },
          DEFAULT_TITLE
        );
        // Extra wait for final React render
        await new Promise(r => setTimeout(r, 1500));
      } catch {
        // Timeout: title stayed default — team may not exist in DB
        console.log(`  ⏳ ${route.padEnd(45)} title unchanged, using fallback`);
        await new Promise(r => setTimeout(r, 2000));
      }
    } else if (isApiPage) {
      // API pages (dashboard, mercado, etc.): fixed wait for data
      await new Promise(r => setTimeout(r, RENDER_WAIT_MS));
    } else {
      // Static pages (blog, sobre, etc.): short wait
      await new Promise(r => setTimeout(r, RENDER_WAIT_STATIC_MS));
    }

    // Get the fully rendered HTML
    // First, de-duplicate meta tags in the DOM (remove originals, keep React-Helmet versions)
    await page.evaluate(() => {
      const head = document.head;
      // Tags managed by React-Helmet have data-rh="true"
      const helmetTags = head.querySelectorAll('[data-rh="true"]');
      if (helmetTags.length === 0) return;

      // Build a set of what Helmet manages
      const managed = new Set();
      helmetTags.forEach(tag => {
        if (tag.tagName === 'LINK' && tag.getAttribute('rel') === 'canonical') {
          managed.add('link-canonical');
        } else if (tag.tagName === 'META') {
          const name = tag.getAttribute('name');
          const prop = tag.getAttribute('property');
          if (name) managed.add(`meta-name-${name}`);
          if (prop) managed.add(`meta-prop-${prop}`);
        }
      });

      // Remove original (non-helmet) tags that conflict — BEFORE stripping data-rh
      const allMeta = head.querySelectorAll('meta:not([data-rh]), link[rel="canonical"]:not([data-rh])');
      allMeta.forEach(tag => {
        if (tag.tagName === 'LINK' && tag.getAttribute('rel') === 'canonical' && managed.has('link-canonical')) {
          tag.remove();
        } else if (tag.tagName === 'META') {
          const name = tag.getAttribute('name');
          const prop = tag.getAttribute('property');
          if (name && managed.has(`meta-name-${name}`)) tag.remove();
          if (prop && managed.has(`meta-prop-${prop}`)) tag.remove();
        }
      });

      // NOW strip data-rh from helmet tags (no longer needed in static HTML)
      helmetTags.forEach(tag => tag.removeAttribute('data-rh'));
    });

    let html = await page.content();

    // Post-process: fix internal URLs
    html = html.replace(/http:\/\/127\.0\.0\.1:\d+/g, 'https://scoutdados.com.br');
    html = html.replace(/ data-reactroot=""/g, '');

    // Determine output path
    const outputPath = route === '/'
      ? join(DIST_DIR, 'index.html')
      : join(DIST_DIR, route.slice(1), 'index.html');

    // Create directory and write file
    const dir = dirname(outputPath);
    mkdirSync(dir, { recursive: true });
    writeFileSync(outputPath, html, 'utf-8');

    // Extract title for logging
    const titleMatch = html.match(/<title>([^<]+)<\/title>/);
    const title = titleMatch ? titleMatch[1].substring(0, 50) : '?';
    const sizeKB = (Buffer.byteLength(html) / 1024).toFixed(1);

    console.log(`  ✅ ${route.padEnd(45)} ${sizeKB.padStart(6)} KB  "${title}"`);
    return true;
  } catch (error) {
    console.error(`  ❌ ${route.padEnd(45)} FAILED: ${error.message}`);
    return false;
  } finally {
    await page.close();
  }
}

// ── Render routes in batches ──
async function renderBatch(browser, baseUrl, routes) {
  const results = await Promise.all(
    routes.map(route => renderRoute(browser, baseUrl, route))
  );
  return results.filter(Boolean).length;
}

// ── Main ──
async function main() {
  console.log('');
  console.log('═══════════════════════════════════════════════════');
  console.log('  ScoutDados — SSG Pre-render');
  console.log('═══════════════════════════════════════════════════');
  console.log('');

  if (process.env.PRERENDER === 'false') {
    console.log('  ⚠️  PRERENDER=false — skipping pre-render');
    process.exit(0);
  }

  if (!existsSync(join(DIST_DIR, 'index.html'))) {
    console.error('  ❌ dist/index.html not found. Run "bun run build" first.');
    process.exit(1);
  }

  // Check API is running
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const res = await fetch(`${API_TARGET}/api/status`, { signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    console.log(`  🔌 Backend API: OK (rodada ${data.rodadaAtual})`);
  } catch (e) {
    console.warn(`  ⚠️  Backend API not reachable: ${e.message} — pages may not have dynamic data`);
  }

  // Build route list
  const autoBlogSlugs = getAutoBlogSlugs();
  const allBlogSlugs = [...new Set([...BLOG_SLUGS, ...autoBlogSlugs])];

  const TEAM_ROUTES = TEAM_SLUGS.map(s => `/brasileirao/time/${s}`);
  const NON_TEAM_ROUTES = [
    ...STATIC_ROUTES,
    ...allBlogSlugs.map(s => `/blog/${s}`),
  ];
  const ALL_ROUTES = [...NON_TEAM_ROUTES, ...TEAM_ROUTES];

  console.log(`  📄 Routes to pre-render: ${ALL_ROUTES.length} (${NON_TEAM_ROUTES.length} static/blog + ${TEAM_ROUTES.length} teams)`);
  console.log('');

  // Start server
  const { server, port } = await startServer();
  const baseUrl = `http://127.0.0.1:${port}`;

  // Launch Puppeteer
  const browser = await launch({
    executablePath: CHROMIUM_PATH,
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-gpu',
      '--disable-dev-shm-usage',
      '--single-process',
    ],
  });

  console.log(`  🌐 Chromium: ${await browser.version()}`);
  console.log(`  ⏱️  Wait: ${RENDER_WAIT_STATIC_MS}ms (static) / smart-wait (API/teams)`);
  console.log('');

  const startTime = Date.now();
  let totalSuccess = 0;

  // Phase 1: Non-team routes in batches of CONCURRENCY
  console.log('  ── Phase 1: Static, API & Blog pages ──');
  for (let i = 0; i < NON_TEAM_ROUTES.length; i += CONCURRENCY) {
    const batch = NON_TEAM_ROUTES.slice(i, i + CONCURRENCY);
    totalSuccess += await renderBatch(browser, baseUrl, batch);
  }

  // Phase 2: Team pages sequentially (sync API can only handle 1 heavy request at a time)
  console.log('  ── Phase 2: Team pages (sequential) ──');
  for (let i = 0; i < TEAM_ROUTES.length; i += CONCURRENCY_TEAM) {
    const batch = TEAM_ROUTES.slice(i, i + CONCURRENCY_TEAM);
    totalSuccess += await renderBatch(browser, baseUrl, batch);
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

  console.log('');
  console.log('═══════════════════════════════════════════════════');
  console.log(`  ✅ Pre-rendered: ${totalSuccess}/${ALL_ROUTES.length} pages in ${elapsed}s`);
  console.log('═══════════════════════════════════════════════════');
  console.log('');

  await browser.close();
  server.close();

  if (totalSuccess < ALL_ROUTES.length) {
    console.warn(`  ⚠️  ${ALL_ROUTES.length - totalSuccess} routes failed`);
  }

  process.exit(totalSuccess === ALL_ROUTES.length ? 0 : 1);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
