import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Brain, 
  TrendingUp, 
  BarChart3, 
  Zap, 
  Target,
  Shield,
  Users,
  Clock,
  ChevronRight,
  Github,
  Mail,
  CheckCircle2,
  Sparkles,
  Trophy
} from "lucide-react";
import { useNavigate, Link } from "react-router-dom";
import { useDashboard } from "@/hooks/useCartolaApi";
import { SEO } from "@/components/SEO";

export default function LandingPage() {
  const navigate = useNavigate();
  const { data: dashboard } = useDashboard();

  const features = [
    {
      icon: Brain,
      title: "Algoritmo Inteligente",
      description: "MPV Calculator analisa preço, média, scouts, tendência e mais 15 fatores para encontrar os melhores jogadores"
    },
    {
      icon: Target,
      title: "2 Times por Rodada",
      description: "Time de Valorização (ganhar C$) e Time de Pontuação (subir no ranking) - estratégias diferentes para cada objetivo"
    },
    {
      icon: BarChart3,
      title: "Análise de Confrontos",
      description: "Força ofensiva/defensiva, mando de campo, chance de SG e expectativa de gols calculados automaticamente"
    },
    {
      icon: TrendingUp,
      title: "Predição de Valorização",
      description: "Identifica jogadores baratos com potencial de valorização baseado em padrões históricos e confrontos"
    },
    {
      icon: Shield,
      title: "Gestão de Risco",
      description: "Evita jogadores suspensos, contundidos ou com baixa probabilidade de jogar"
    },
    {
      icon: Clock,
      title: "Atualização em Tempo Real",
      description: "Dados sincronizados com a API oficial do Cartola FC a cada 5 minutos"
    }
  ];

  const steps = [
    {
      number: "1",
      title: "Escolha o Esquema",
      description: "Selecione sua formação preferida: 4-4-2, 4-3-3, 3-5-2 e outras"
    },
    {
      number: "2", 
      title: "Defina o Orçamento",
      description: "Informe quantas cartoletas você tem disponíveis"
    },
    {
      number: "3",
      title: "Algoritmo Analisa",
      description: "Processamos 500+ jogadores em segundos"
    },
    {
      number: "4",
      title: "Receba 2 Times",
      description: "Um para valorização e outro para pontuação máxima"
    }
  ];

  const faqs = [
    {
      question: "É realmente grátis?",
      answer: "Sim! 100% gratuito, sem limite de uso. Nosso objetivo é ajudar a comunidade do Cartola FC."
    },
    {
      question: "Como funciona o algoritmo?",
      answer: "Analisamos 20+ fatores incluindo preço, média, scouts, tendência, confronto, mando de campo, forma do time e muito mais."
    },
    {
      question: "É permitido pela Globo?",
      answer: "Sim! Usamos apenas dados públicos disponibilizados pela API oficial do Cartola FC."
    },
    {
      question: "Preciso criar conta?",
      answer: "Não! Acesse direto e gere seus times sem nenhum cadastro."
    },
    {
      question: "Com que frequência os dados são atualizados?",
      answer: "Os dados são sincronizados com a API do Cartola a cada 5 minutos durante o período do mercado aberto."
    },
    {
      question: "Posso usar em qualquer rodada?",
      answer: "Sim! O sistema funciona durante todo o Brasileirão 2026, atualizando automaticamente a cada rodada."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-green-950/20 via-background to-background">
      <SEO path="/" />
      {/* Header/Nav */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-green-600 flex items-center justify-center">
              <span className="text-white font-bold">S</span>
            </div>
            <span className="font-bold text-xl">ScoutDados</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link to="/brasileirao" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Brasileirão
            </Link>
            <Link to="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Dashboard
            </Link>
            <Link to="/escalacao" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Escalação
            </Link>
            <Link to="/confrontos" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Confrontos
            </Link>
            <Link to="/scouts" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Scouts
            </Link>
            <Link to="/mercado" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Mercado
            </Link>
            <Link to="/blog" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Blog
            </Link>
          </nav>
          <Button onClick={() => navigate('/escalacao')} className="bg-green-600 hover:bg-green-700">
            Gerar Time
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 md:py-24">
        <div className="text-center max-w-4xl mx-auto">
          <Badge variant="secondary" className="mb-4 gap-1">
            <Sparkles className="w-3 h-3" />
            100% Gratuito
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-green-400 to-emerald-600 bg-clip-text text-transparent leading-tight">
            Estatísticas do Brasileirão &<br />Inteligência para o Cartola
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Classificação com <strong>simulação Monte Carlo</strong>, previsão de placares, análise de scouts e escalação inteligente para o Cartola FC 2026 — completamente grátis.
          </p>
          
          {/* Stats Badge */}
          {dashboard && (
            <div className="flex flex-wrap justify-center gap-4 mb-8">
              <Badge variant="outline" className="text-sm py-1 px-3">
                Rodada {dashboard.mercado?.rodadaAtual || '-'}
              </Badge>
              <Badge variant="outline" className="text-sm py-1 px-3">
                {dashboard.mercado?.totalAtletas?.toLocaleString() || '500+'} jogadores
              </Badge>
              <Badge variant="outline" className="text-sm py-1 px-3 capitalize">
                Mercado {dashboard.mercado?.status || 'ativo'}
              </Badge>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg" 
              className="gap-2 text-lg px-8 py-6 bg-green-600 hover:bg-green-700"
              onClick={() => navigate('/brasileirao')}
            >
              <Trophy className="w-5 h-5" />
              Ver Brasileirão
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              className="gap-2 text-lg px-8 py-6"
              onClick={() => navigate('/escalacao')}
            >
              <Zap className="w-5 h-5" />
              Gerar Escalação
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              className="gap-2 text-lg px-8 py-6"
              onClick={() => navigate('/dashboard')}
            >
              <BarChart3 className="w-5 h-5" />
              Dashboard
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-16 md:py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Por Que Usar ScoutDados?
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Ferramentas profissionais de análise que antes só estavam disponíveis para experts, agora de graça para todos.
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="bg-card/50 backdrop-blur border-muted hover:border-green-600/50 transition-colors">
              <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-green-600/10 flex items-center justify-center mb-3">
                  <feature.icon className="w-6 h-6 text-green-500" />
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* How it Works */}
      <section className="container mx-auto px-4 py-16 md:py-20 bg-muted/30 rounded-3xl">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Como Funciona
          </h2>
          <p className="text-muted-foreground">
            4 passos simples para escalar seu time campeão
          </p>
        </div>
        <div className="grid md:grid-cols-4 gap-8 max-w-5xl mx-auto">
          {steps.map((step, index) => (
            <div key={index} className="text-center">
              <div className="w-16 h-16 rounded-full bg-green-600 text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                {step.number}
              </div>
              <h3 className="font-semibold text-lg mb-2">{step.title}</h3>
              <p className="text-muted-foreground text-sm">{step.description}</p>
            </div>
          ))}
        </div>
        <div className="text-center mt-12">
          <Button 
            size="lg" 
            className="gap-2 bg-green-600 hover:bg-green-700"
            onClick={() => navigate('/escalacao')}
          >
            Começar Agora
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="container mx-auto px-4 py-16 md:py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Perguntas Frequentes
          </h2>
        </div>
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {faqs.map((faq, index) => (
            <Card key={index} className="bg-card/50">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-start gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 shrink-0" />
                  {faq.question}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground pl-7">{faq.answer}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16 md:py-20">
        <Card className="bg-gradient-to-r from-green-600/10 to-emerald-600/10 border-green-600/20">
          <CardContent className="py-12 text-center">
            <h2 className="text-3xl font-bold mb-4">
              Pronto para Dominar o Brasileirão?
            </h2>
            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
              Classificação com probabilidades, previsão de placares e escalação 
              inteligente para o Cartola FC — tudo grátis e atualizado a cada rodada.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg" 
                className="gap-2 text-lg px-8 py-6 bg-green-600 hover:bg-green-700"
                onClick={() => navigate('/brasileirao')}
              >
                <Trophy className="w-5 h-5" />
                Ver Classificação
              </Button>
              <Button 
                size="lg" 
                variant="outline"
                className="gap-2 text-lg px-8 py-6"
                onClick={() => navigate('/escalacao')}
              >
                <Zap className="w-5 h-5" />
                Gerar Escalação Grátis
              </Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t bg-muted/30">
        <div className="container mx-auto px-4 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-green-600 flex items-center justify-center">
                  <span className="text-white font-bold">S</span>
                </div>
                <span className="font-bold text-xl">ScoutDados</span>
              </div>
              <p className="text-muted-foreground text-sm mb-4">
                Estatísticas do Brasileirão 2026 e ferramentas inteligentes para Cartola FC.
                Classificação, previsões, scouts e escalações otimizadas.
              </p>
              <p className="text-xs text-muted-foreground">
                Este site não é afiliado, endossado ou patrocinado pela Globo ou Cartola FC. 
                Todos os dados são obtidos através da API pública do Cartola.
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="font-semibold mb-4">Navegação</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/brasileirao" className="text-muted-foreground hover:text-foreground transition-colors">
                    Brasileirão
                  </Link>
                </li>
                <li>
                  <Link to="/dashboard" className="text-muted-foreground hover:text-foreground transition-colors">
                    Dashboard
                  </Link>
                </li>
                <li>
                  <Link to="/escalacao" className="text-muted-foreground hover:text-foreground transition-colors">
                    Gerar Escalação
                  </Link>
                </li>
                <li>
                  <Link to="/confrontos" className="text-muted-foreground hover:text-foreground transition-colors">
                    Confrontos
                  </Link>
                </li>
                <li>
                  <Link to="/scouts" className="text-muted-foreground hover:text-foreground transition-colors">
                    Scouts & Análises
                  </Link>
                </li>
                <li>
                  <Link to="/mercado" className="text-muted-foreground hover:text-foreground transition-colors">
                    Mercado
                  </Link>
                </li>
              </ul>
            </div>

            {/* Info */}
            <div>
              <h4 className="font-semibold mb-4">Informações</h4>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link to="/sobre" className="text-muted-foreground hover:text-foreground transition-colors">
                    Sobre
                  </Link>
                </li>
                <li>
                  <Link to="/privacidade" className="text-muted-foreground hover:text-foreground transition-colors">
                    Política de Privacidade
                  </Link>
                </li>
                <li>
                  <Link to="/termos" className="text-muted-foreground hover:text-foreground transition-colors">
                    Termos de Uso
                  </Link>
                </li>
                <li>
                  <a 
                    href="mailto:contato@scoutdados.com.br" 
                    className="text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
                  >
                    <Mail className="w-3 h-3" />
                    Contato
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t mt-8 pt-8 text-center text-sm text-muted-foreground">
            <p>© 2026 ScoutDados. Todos os direitos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
