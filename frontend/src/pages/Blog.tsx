import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Calendar, Clock, Tag, Newspaper } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SEO } from "@/components/SEO";
import { MainLayout } from "@/components/layout/MainLayout";
import { posts } from "@/content/posts";

export default function Blog() {
  return (
    <MainLayout>
      <SEO
        title="Blog"
        description="Artigos sobre estatísticas de futebol, Monte Carlo, xG, Cartola FC e previsões do Brasileirão 2026."
        path="/blog"
      />

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 hero-gradient rounded-lg">
            <Newspaper className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">Blog</h1>
            <p className="text-muted-foreground">
              Artigos sobre estatísticas, modelos e estratégias de futebol
            </p>
          </div>
        </div>
      </motion.div>

      {/* Posts Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {posts.map((post, i) => (
          <motion.div
            key={post.slug}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Link to={`/blog/${post.slug}`} className="block group">
              <Card className="h-full transition-all duration-300 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-3 text-xs text-muted-foreground mb-2">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(post.date).toLocaleDateString("pt-BR", {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {post.readTime} min de leitura
                    </span>
                  </div>
                  <h2 className="font-display text-xl font-bold group-hover:text-primary transition-colors">
                    {post.title}
                  </h2>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm mb-4">
                    {post.excerpt}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {post.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        <Tag className="w-3 h-3 mr-1" />
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="mt-12 p-4 rounded-lg bg-muted/50 border text-xs text-muted-foreground text-center">
        As projeções apresentadas nos artigos são resultado de modelos estatísticos (Poisson, Monte Carlo) com fins informativos e educacionais.
        Não representam garantia de resultado e não devem ser utilizadas para fins de apostas.
      </div>
    </MainLayout>
  );
}
