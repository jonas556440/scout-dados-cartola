import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Brain, 
  Target, 
  BarChart3, 
  Github, 
  Mail, 
  Heart,
  Code,
  Database,
  Zap,
  ArrowLeft
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

export default function Sobre() {
  const navigate = useNavigate();

  const techStack = [
    { name: "FastAPI", description: "Backend Python de alta performance", icon: Zap },
    { name: "React", description: "Interface moderna e responsiva", icon: Code },
    { name: "SQLite", description: "Banco de dados local eficiente", icon: Database },
    { name: "TanStack Query", description: "Gerenciamento de estado e cache", icon: Brain },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-green-600 flex items-center justify-center">
              <span className="text-white font-bold">S</span>
            </div>
            <span className="font-bold text-xl">ScoutDados</span>
          </Link>
          <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Hero */}
        <div className="text-center mb-12">
          <Badge variant="secondary" className="mb-4">Sobre o Projeto</Badge>
          <h1 className="text-4xl font-bold mb-4">ScoutDados</h1>
          <p className="text-xl text-muted-foreground">
            Sistema de análise inteligente para Cartola FC 2026
          </p>
        </div>

        {/* Mission */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-green-500" />
              Nossa Missão
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              O ScoutDados nasceu da paixão pelo Cartola FC e pela análise de dados. 
              Nossa missão é democratizar o acesso a ferramentas avançadas de análise 
              que antes só estavam disponíveis para poucos.
            </p>
            <p className="text-muted-foreground">
              Acreditamos que todos os cartoleiros merecem ter acesso às mesmas 
              ferramentas de análise, independente de conhecimento técnico ou recursos.
              Por isso, oferecemos tudo <strong>100% gratuito</strong>.
            </p>
          </CardContent>
        </Card>

        {/* Features */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-green-500" />
              O Que Oferecemos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">•</span>
                <span><strong>Algoritmo MPV:</strong> Calcula o Melhor Preço x Valorização para cada jogador</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">•</span>
                <span><strong>Dois Times por Rodada:</strong> Um focado em valorização (ganhar C$) e outro em pontuação máxima</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">•</span>
                <span><strong>Análise de Confrontos:</strong> Força ofensiva/defensiva, mando de campo, chance de SG</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">•</span>
                <span><strong>Dados em Tempo Real:</strong> Sincronização com API oficial do Cartola</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-1">•</span>
                <span><strong>Histórico Completo:</strong> Acompanhe sua evolução ao longo das rodadas</span>
              </li>
            </ul>
          </CardContent>
        </Card>

        {/* Tech Stack */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="w-5 h-5 text-green-500" />
              Tecnologias
            </CardTitle>
            <CardDescription>
              Construído com tecnologias modernas e de alta performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {techStack.map((tech, index) => (
                <div key={index} className="text-center p-4 rounded-lg bg-muted/50">
                  <tech.icon className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  <h4 className="font-medium text-sm">{tech.name}</h4>
                  <p className="text-xs text-muted-foreground">{tech.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Data Source */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-green-500" />
              Fonte dos Dados
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Todos os dados de jogadores, times, partidas e pontuações são obtidos 
              através da <strong>API pública oficial do Cartola FC</strong>, disponibilizada 
              pela Globo em <code className="bg-muted px-1 rounded">api.cartolafc.globo.com</code>.
            </p>
            <p className="text-muted-foreground">
              Os dados são atualizados automaticamente a cada 5 minutos durante o 
              período de mercado aberto, garantindo que você sempre tenha acesso 
              às informações mais recentes.
            </p>
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <Card className="mb-8 border-yellow-600/30 bg-yellow-600/5">
          <CardHeader>
            <CardTitle className="text-yellow-600">⚠️ Aviso Legal</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>
              Este site <strong>não é afiliado, endossado ou patrocinado</strong> pela 
              Globo, Cartola FC ou qualquer uma de suas subsidiárias.
            </p>
            <p>
              "Cartola FC" é uma marca registrada da Globo Comunicação e Participações S.A.
              Usamos o nome apenas para fins informativos e de referência.
            </p>
            <p>
              Os algoritmos de análise e predição são desenvolvidos de forma independente 
              e não garantem resultados. Use as sugestões como uma ferramenta adicional 
              de apoio à decisão.
            </p>
          </CardContent>
        </Card>

        {/* Contact */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-green-500" />
              Contato
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Tem sugestões, encontrou algum bug ou quer contribuir com o projeto?
              Entre em contato conosco!
            </p>
            <div className="flex flex-wrap gap-4">
              <Button variant="outline" asChild>
                <a href="mailto:contato@scoutdados.com.br" className="gap-2">
                  <Mail className="w-4 h-4" />
                  contato@scoutdados.com.br
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer note */}
        <div className="text-center mt-12 text-sm text-muted-foreground">
          <p className="flex items-center justify-center gap-1">
            Feito com <Heart className="w-4 h-4 text-red-500" /> para a comunidade do Cartola FC
          </p>
        </div>
      </main>
    </div>
  );
}
