import { MainLayout } from "@/components/layout/MainLayout";
import { FileText, AlertTriangle, Scale, Code, Server, Shield } from "lucide-react";
import { SEO } from "@/components/SEO";

const Termos = () => {
  return (
    <MainLayout>
      <SEO title="Termos de Uso" description="Termos de uso do ScoutDados. Condições de utilização da plataforma de estatísticas do Brasileirão e Cartola FC." path="/termos" />
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 hero-gradient rounded-lg">
            <FileText className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-3xl font-bold">Termos de Uso</h1>
            <p className="text-muted-foreground">Última atualização: 7 de fevereiro de 2026</p>
          </div>
        </div>

        <div className="prose prose-invert max-w-none space-y-8">
          {/* Aceitação */}
          <section className="glass-card p-6">
            <h2 className="font-display text-xl font-bold mb-4">1. Aceitação dos Termos</h2>
            <p className="text-muted-foreground leading-relaxed">
              Ao acessar e utilizar o <strong>ScoutDados</strong> (scoutdados.com.br), você
              concorda com estes Termos de Uso. Se não concordar com qualquer ponto,
              por favor, não utilize o site. O uso continuado constitui aceitação dos
              termos em vigor.
            </p>
          </section>

          {/* Descrição do Serviço */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Server className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold m-0">2. Descrição do Serviço</h2>
            </div>
            <p className="text-muted-foreground mb-3">
              O ScoutDados é um portal gratuito de:
            </p>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li>Estatísticas e análises do Campeonato Brasileiro</li>
              <li>Ferramentas para o jogo Cartola FC (fantasy game da Globo)</li>
              <li>Projeções estatísticas baseadas em modelos probabilísticos (Poisson, Monte Carlo)</li>
              <li>Simulador de jogos e previsões de placares</li>
            </ul>
          </section>

          {/* Isenção de Responsabilidade */}
          <section className="glass-card p-6 border border-warning/30">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-warning" />
              <h2 className="font-display text-xl font-bold m-0 text-warning">3. Isenção de Responsabilidade</h2>
            </div>
            <div className="bg-warning/10 border border-warning/20 rounded-lg p-4 mb-4">
              <p className="text-sm text-muted-foreground leading-relaxed">
                <strong>As projeções apresentadas são resultado de modelos estatísticos (Poisson, Monte Carlo)
                com fins informativos e educacionais. Não representam garantia de resultado e não devem
                ser utilizadas para fins de apostas.</strong>
              </p>
            </div>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li>O ScoutDados <strong>não é</strong> uma casa de apostas e <strong>não promove</strong> apostas de qualquer natureza</li>
              <li>Probabilidades e previsões são puramente estatísticas, calculadas internamente pelo nosso modelo</li>
              <li>Resultados passados não garantem resultados futuros</li>
              <li>O usuário assume total responsabilidade pelo uso das informações</li>
              <li>O ScoutDados não se responsabiliza por decisões tomadas com base nas projeções</li>
            </ul>
          </section>

          {/* Proibições */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-destructive" />
              <h2 className="font-display text-xl font-bold m-0">4. Uso Proibido</h2>
            </div>
            <p className="text-muted-foreground mb-3">É expressamente proibido:</p>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li>Utilizar o conteúdo para promover apostas ou jogos de azar</li>
              <li>Reproduzir, distribuir ou comercializar dados do site sem autorização</li>
              <li>Realizar scraping automatizado ou acessar a API de forma abusiva</li>
              <li>Exceder os limites de requisições da API pública (/docs)</li>
              <li>Utilizar o site para atividades ilegais ou que violem direitos de terceiros</li>
            </ul>
          </section>

          {/* Propriedade Intelectual */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Code className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold m-0">5. Propriedade Intelectual</h2>
            </div>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li><strong>Algoritmos e código:</strong> Os modelos preditivos, algoritmos de análise e código-fonte são propriedade do ScoutDados</li>
              <li><strong>Conteúdo editorial:</strong> Textos, análises e conteúdo do blog são protegidos por direitos autorais (©)</li>
              <li><strong>Dados de terceiros:</strong> Dados de jogadores, times e partidas são fornecidos por fontes públicas (API Cartola FC/Globo, football-data.org) e pertencem a seus respectivos detentores</li>
              <li><strong>Escudos e logos:</strong> São propriedade de seus respectivos clubes e federações</li>
            </ul>
          </section>

          {/* API Pública */}
          <section className="glass-card p-6">
            <h2 className="font-display text-xl font-bold mb-4">6. Uso da API</h2>
            <p className="text-muted-foreground mb-3">
              O ScoutDados disponibiliza uma API pública documentada em{" "}
              <a href="/docs" className="text-primary hover:underline">/docs</a>. Ao usar a API:
            </p>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li>Respeite os limites de requisições (rate limiting)</li>
              <li>Não sobrecarregue os servidores com requests excessivos</li>
              <li>Dê atribuição ao ScoutDados ao exibir dados publicamente</li>
              <li>Não utilize para fins comerciais sem autorização prévia</li>
            </ul>
          </section>

          {/* Disponibilidade */}
          <section className="glass-card p-6">
            <h2 className="font-display text-xl font-bold mb-4">7. Disponibilidade</h2>
            <p className="text-muted-foreground">
              O ScoutDados é oferecido "como está" (as is), sem garantias de disponibilidade
              ininterrupta. Podemos realizar manutenções, atualizações ou suspender funcionalidades
              a qualquer momento. As fontes de dados externas (API Cartola FC, football-data.org)
              podem sofrer indisponibilidades fora do nosso controle.
            </p>
          </section>

          {/* Modificações */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Scale className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold m-0">8. Alterações nos Termos</h2>
            </div>
            <p className="text-muted-foreground">
              Reservamo-nos o direito de modificar estes termos a qualquer momento. Alterações
              significativas serão comunicadas no site. O uso continuado após as alterações
              implica aceitação dos novos termos. A data da última atualização é sempre indicada no topo.
            </p>
          </section>

          {/* Lei Aplicável */}
          <section className="glass-card p-6">
            <h2 className="font-display text-xl font-bold mb-4">9. Lei Aplicável</h2>
            <p className="text-muted-foreground">
              Estes termos são regidos pelas leis da República Federativa do Brasil. Quaisquer
              disputas deverão ser submetidas ao foro da comarca do domicílio do administrador do site.
            </p>
          </section>

          {/* Contato */}
          <section className="glass-card p-6">
            <h2 className="font-display text-xl font-bold mb-4">10. Contato</h2>
            <p className="text-muted-foreground">
              Dúvidas ou solicitações sobre estes termos podem ser enviadas para:{" "}
              <a href="mailto:contato@scoutdados.com.br" className="text-primary hover:underline">
                contato@scoutdados.com.br
              </a>
            </p>
          </section>
        </div>
      </div>
    </MainLayout>
  );
};

export default Termos;
