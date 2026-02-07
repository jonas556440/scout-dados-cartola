import { Helmet } from "react-helmet-async";

interface SEOProps {
  title?: string;
  description?: string;
  path?: string;
  image?: string;
  /** Tipo OG: 'website' (padrão) ou 'article' para blog posts */
  type?: "website" | "article";
  /** Data de publicação ISO para articles */
  publishedTime?: string;
  /** Tags/keywords do artigo */
  tags?: string[];
}

const BASE_TITLE = "ScoutDados";
const BASE_URL = "https://scoutdados.com.br";
const DEFAULT_DESCRIPTION = "Classificação do Brasileirão 2026 com simulação Monte Carlo, previsão de placares, scouts e escalação inteligente para Cartola FC. 100% gratuito.";
const DEFAULT_IMAGE = `${BASE_URL}/og-image.png`;

export function SEO({ title, description, path = "", image, type = "website", publishedTime, tags }: SEOProps) {
  const fullTitle = title ? `${title} | ${BASE_TITLE}` : `${BASE_TITLE} - Brasileirão 2026 & Cartola FC`;
  const fullDescription = description || DEFAULT_DESCRIPTION;
  const url = `${BASE_URL}${path}`;
  const ogImage = image || DEFAULT_IMAGE;

  // JSON-LD Article para blog posts
  const articleJsonLd = type === "article" ? JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": title || fullTitle,
    "description": fullDescription,
    "image": ogImage,
    "url": url,
    "datePublished": publishedTime || new Date().toISOString(),
    "dateModified": publishedTime || new Date().toISOString(),
    "author": { "@type": "Organization", "name": "ScoutDados" },
    "publisher": {
      "@type": "Organization",
      "name": "ScoutDados",
      "url": BASE_URL,
    },
    "mainEntityOfPage": { "@type": "WebPage", "@id": url },
    ...(tags?.length ? { "keywords": tags.join(", ") } : {}),
  }) : null;

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={fullDescription} />
      <link rel="canonical" href={url} />

      {/* Open Graph */}
      <meta property="og:type" content={type} />
      <meta property="og:url" content={url} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={fullDescription} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:site_name" content="ScoutDados" />
      <meta property="og:locale" content="pt_BR" />
      {type === "article" && publishedTime && (
        <meta property="article:published_time" content={publishedTime} />
      )}

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={fullDescription} />
      <meta name="twitter:image" content={ogImage} />

      {/* JSON-LD Article */}
      {articleJsonLd && (
        <script type="application/ld+json">{articleJsonLd}</script>
      )}
    </Helmet>
  );
}
