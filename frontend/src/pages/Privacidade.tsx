import { MainLayout } from "@/components/layout/MainLayout";
import { Shield, Cookie, Eye, Database, Lock, ExternalLink } from "lucide-react";

const Privacidade = () => {
  return (
    <MainLayout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 hero-gradient rounded-lg">
            <Shield className="w-6 h-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-3xl font-bold">Política de Privacidade</h1>
            <p className="text-muted-foreground">Última atualização: 7 de fevereiro de 2026</p>
          </div>
        </div>

        <div className="prose prose-invert max-w-none space-y-8">
          {/* Introdução */}
          <section className="glass-card p-6">
            <p className="text-muted-foreground leading-relaxed">
              O <strong>ScoutDados</strong> (scoutdados.com.br) é um portal de estatísticas
              de futebol e ferramentas para o Cartola FC. Esta política descreve quais dados
              coletamos, como os utilizamos e seus direitos enquanto usuário, em conformidade
              com a <strong>Lei Geral de Proteção de Dados (LGPD — Lei nº 13.709/2018)</strong>.
            </p>
          </section>

          {/* Cookies */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Cookie className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold m-0">1. Cookies e Tecnologias de Rastreamento</h2>
            </div>

            <h3 className="text-lg font-semibold mt-4 mb-2">Google Analytics (GA4)</h3>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li><strong>Finalidade:</strong> Métricas de uso, origens de tráfego, páginas mais visitadas</li>
              <li><strong>Dados coletados:</strong> Páginas visitadas, tempo de sessão, tipo de dispositivo, localização aproximada (país/estado)</li>
              <li><strong>Retenção:</strong> 14 meses (padrão GA4)</li>
              <li><strong>Opt-out:</strong> Extensão <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Google Analytics Opt-out <ExternalLink className="inline w-3 h-3" /></a></li>
            </ul>

            <h3 className="text-lg font-semibold mt-4 mb-2">Google AdSense</h3>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li><strong>Finalidade:</strong> Exibição de anúncios relevantes</li>
              <li><strong>Cookies de publicidade:</strong> Personalizada ou contextual, conforme sua escolha</li>
              <li><strong>Como desativar:</strong> <a href="https://adssettings.google.com/" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Google Ad Settings <ExternalLink className="inline w-3 h-3" /></a></li>
            </ul>

            <h3 className="text-lg font-semibold mt-4 mb-2">Cookies Essenciais</h3>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li><strong>scoutdados-consent:</strong> Armazena sua escolha de consentimento de cookies</li>
              <li><strong>Cache local (localStorage):</strong> Preferências de interface e cache de dados da API para melhor desempenho</li>
            </ul>
          </section>

          {/* Dados Coletados */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Database className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold m-0">2. Dados Coletados</h2>
            </div>

            <h3 className="text-lg font-semibold mt-4 mb-2">Endereço IP</h3>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li><strong>Armazenamento:</strong> Anonimizado (últimos octetos mascarados)</li>
              <li><strong>Finalidade:</strong> Prevenção de abuso (rate limiting), segurança da aplicação</li>
              <li><strong>Não utilizado para:</strong> Geolocalização individual ou identificação pessoal</li>
            </ul>

            <h3 className="text-lg font-semibold mt-4 mb-2">Dados do Cartola FC</h3>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li>O ScoutDados <strong>não</strong> armazena login, senha ou dados pessoais de contas Cartola</li>
              <li>Apenas consulta dados públicos via API Cartola FC (Globo)</li>
              <li>Dados de atletas, preços e scouts são informações públicas da API</li>
            </ul>
          </section>

          {/* Compartilhamento */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Eye className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold m-0">3. Compartilhamento de Dados</h2>
            </div>
            <ul className="list-disc pl-6 space-y-2 text-muted-foreground">
              <li><strong>Não vendemos dados.</strong> Nenhum dado pessoal é comercializado.</li>
              <li>Dados são compartilhados apenas com Google (Analytics e AdSense) para fins de métricas e publicidade</li>
              <li>Não compartilhamos dados com nenhum outro terceiro</li>
            </ul>
          </section>

          {/* Direitos do Usuário */}
          <section className="glass-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Lock className="w-5 h-5 text-primary" />
              <h2 className="font-display text-xl font-bold m-0">4. Seus Direitos (LGPD)</h2>
            </div>
            <p className="text-muted-foreground mb-3">
              De acordo com a LGPD (Lei nº 13.709/2018), você tem direito a:
            </p>
            <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
              <li>Confirmar a existência de tratamento de seus dados</li>
              <li>Acessar, corrigir ou solicitar a exclusão de seus dados</li>
              <li>Revogar o consentimento a qualquer momento</li>
              <li>Solicitar a portabilidade de dados</li>
              <li>Obter informações sobre com quem seus dados são compartilhados</li>
            </ul>
            <p className="text-muted-foreground mt-3">
              Para exercer qualquer um destes direitos, entre em contato pelo e-mail:{" "}
              <a href="mailto:privacidade@scoutdados.com.br" className="text-primary hover:underline">
                privacidade@scoutdados.com.br
              </a>
            </p>
          </section>

          {/* Segurança */}
          <section className="glass-card p-6">
            <h2 className="font-display text-xl font-bold mb-4">5. Segurança</h2>
            <p className="text-muted-foreground">
              Utilizamos medidas técnicas e organizacionais para proteger seus dados,
              incluindo: HTTPS (TLS 1.3), headers de segurança (HSTS, CSP, X-Frame-Options),
              rate limiting para prevenção de abuso, e anonimização de dados de acesso.
            </p>
          </section>

          {/* Alterações */}
          <section className="glass-card p-6">
            <h2 className="font-display text-xl font-bold mb-4">6. Alterações Nesta Política</h2>
            <p className="text-muted-foreground">
              Esta política pode ser atualizada periodicamente. A data da última atualização
              será sempre indicada no topo da página. Recomendamos a revisão periódica.
            </p>
          </section>

          {/* Atribuições */}
          <section className="glass-card p-6">
            <h2 className="font-display text-xl font-bold mb-4">7. Fontes de Dados e Atribuição</h2>
            <p className="text-muted-foreground">
              Escudos e logos são propriedade de seus respectivos clubes. Dados fornecidos
              por API Cartola FC (Globo), football-data.org e fontes públicas.
              As projeções estatísticas são resultado de modelos internos (Poisson, Monte Carlo)
              com fins informativos e educacionais.
            </p>
          </section>
        </div>
      </div>
    </MainLayout>
  );
};

export default Privacidade;
