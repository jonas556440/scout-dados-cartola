"""
Scheduler Service - Serviço de Background para Monitoramento
Cartola FC 2026

Responsabilidades:
1. Verificar se mercado fechou
2. Salvar escalação final antes do fechamento
3. Após rodada encerrar: coletar pontuações e salvar no histórico
4. Monitorar mudanças de status (provável -> dúvida -> suspenso)
5. Notificar sobre mudanças importantes

Executa tarefas em background usando APScheduler
"""
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import time

sys.path.append(str(Path(__file__).parent))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from src.api.cartola_api import CartolaAPI
from src.analysis.team_selector import TeamSelector
from src.analysis.mpv_calculator import MPVCalculator
from src.database.history_manager import HistoryManager
from src.database.db_manager import DatabaseManager
from config.settings import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CartolaScheduler')


class CartolaScheduler:
    """
    Serviço de background que monitora o Cartola FC
    e executa tarefas automaticamente
    """
    
    def __init__(self):
        self.api = CartolaAPI()
        self.team_selector = TeamSelector()
        self.mpv_calculator = MPVCalculator()
        self.history = HistoryManager()
        self.db = DatabaseManager()
        
        self.scheduler = BackgroundScheduler()
        self.ultima_verificacao_mercado = None
        self.mercado_fechado_salvo = False
        self.rodada_atual = None
        self.status_atletas = {}  # Cache de status dos atletas
        
    def iniciar(self):
        """Inicia o scheduler com todas as tarefas"""
        logger.info("=" * 60)
        logger.info("🚀 Iniciando Cartola Scheduler Service")
        logger.info("=" * 60)
        
        # Tarefa 1: Verificar status do mercado a cada 5 minutos
        self.scheduler.add_job(
            func=self.verificar_status_mercado,
            trigger=IntervalTrigger(minutes=5),
            id='verificar_mercado',
            name='Verificar Status do Mercado',
            replace_existing=True
        )
        logger.info("✅ Job 'verificar_mercado' agendado (a cada 5 min)")
        
        # Tarefa 2: Monitorar mudanças de status dos atletas (a cada 10 min)
        self.scheduler.add_job(
            func=self.monitorar_status_atletas,
            trigger=IntervalTrigger(minutes=10),
            id='monitorar_atletas',
            name='Monitorar Status dos Atletas',
            replace_existing=True
        )
        logger.info("✅ Job 'monitorar_atletas' agendado (a cada 10 min)")
        
        # Tarefa 3: Salvar escalação 1h antes do fechamento
        # (Será agendada dinamicamente quando soubermos o horário)
        
        # Tarefa 4: Coletar pontuações após jogos (a cada hora durante rodada)
        self.scheduler.add_job(
            func=self.coletar_pontuacoes_rodada,
            trigger=IntervalTrigger(hours=1),
            id='coletar_pontuacoes',
            name='Coletar Pontuações da Rodada',
            replace_existing=True
        )
        logger.info("✅ Job 'coletar_pontuacoes' agendado (a cada 1h)")
        
        # Tarefa 5: Backup diário às 03:00
        self.scheduler.add_job(
            func=self.backup_diario,
            trigger=CronTrigger(hour=3, minute=0),
            id='backup_diario',
            name='Backup Diário do Banco',
            replace_existing=True
        )
        logger.info("✅ Job 'backup_diario' agendado (03:00 diariamente)")
        
        # Tarefa 6: Atualizar dados completos do mercado (a cada 30 min)
        self.scheduler.add_job(
            func=self.atualizar_dados_mercado,
            trigger=IntervalTrigger(minutes=30),
            id='atualizar_mercado',
            name='Atualizar Dados do Mercado',
            replace_existing=True
        )
        logger.info("✅ Job 'atualizar_mercado' agendado (a cada 30 min)")
        
        # Tarefa 7: Buscar notícias dos times (a cada 2 horas)
        self.scheduler.add_job(
            func=self.buscar_noticias_times,
            trigger=IntervalTrigger(hours=2),
            id='buscar_noticias',
            name='Buscar Notícias dos Times',
            replace_existing=True
        )
        logger.info("✅ Job 'buscar_noticias' agendado (a cada 2h)")
        
        # Tarefa 8: Atualizar força e classificação dos times (a cada 1 hora)
        self.scheduler.add_job(
            func=self.atualizar_classificacao_times,
            trigger=IntervalTrigger(hours=1),
            id='atualizar_classificacao',
            name='Atualizar Classificação e Força dos Times',
            replace_existing=True
        )
        logger.info("✅ Job 'atualizar_classificacao' agendado (a cada 1h)")
        
        # Tarefa 9: Limpar cache da API (a cada 15 min)
        self.scheduler.add_job(
            func=self.limpar_cache_api,
            trigger=IntervalTrigger(minutes=15),
            id='limpar_cache',
            name='Limpar Cache da API',
            replace_existing=True
        )
        logger.info("✅ Job 'limpar_cache' agendado (a cada 15 min)")
        
        # Tarefa 10: Regenerar sitemap a cada 6h
        self.scheduler.add_job(
            func=self.regenerar_sitemap,
            trigger=CronTrigger(hour='*/6', minute=15),
            id='regenerar_sitemap',
            name='Regenerar Sitemap XML',
            replace_existing=True
        )
        logger.info("✅ Job 'regenerar_sitemap' agendado (a cada 6h)")
        
        # Iniciar scheduler
        self.scheduler.start()
        logger.info("🟢 Scheduler ATIVO - Monitoramento em execução")
        logger.info("=" * 60)
        
        # Executar primeira verificação imediatamente
        self.verificar_status_mercado()
        self.atualizar_dados_mercado()  # Carregar dados iniciais
    
    def parar(self):
        """Para o scheduler"""
        logger.info("🛑 Parando Cartola Scheduler...")
        self.scheduler.shutdown()
        logger.info("✅ Scheduler finalizado")
    
    # ==================== VERIFICAÇÃO DE MERCADO ====================
    
    def verificar_status_mercado(self):
        """
        Verifica status do mercado e toma ações baseadas no estado
        """
        try:
            logger.info("🔍 Verificando status do mercado...")
            
            status = self.api.get_status_mercado()
            if not status:
                logger.warning("⚠️  API indisponível - aguardando próxima verificação")
                return
            
            rodada_atual = status.get("rodada_atual", 0)
            status_mercado = status.get("status_mercado", 0)
            fechamento_ts = status.get("fechamento", {}).get("timestamp", 0)
            
            # Status: 1=aberto, 2=fechando, 4=fechado
            status_nome = {1: "ABERTO", 2: "FECHANDO", 4: "FECHADO"}.get(status_mercado, "DESCONHECIDO")
            
            self.rodada_atual = rodada_atual
            fechamento = datetime.fromtimestamp(fechamento_ts)
            agora = datetime.now()
            tempo_restante = fechamento - agora
            
            logger.info(f"📊 Rodada {rodada_atual} | Status: {status_nome} | Fecha em: {fechamento.strftime('%d/%m %H:%M')}")
            
            # Ação 1: Se falta 1h para fechar e não salvamos ainda
            if tempo_restante <= timedelta(hours=1) and not self.mercado_fechado_salvo:
                logger.warning(f"⚠️  ATENÇÃO: Mercado fecha em {tempo_restante}! Salvando escalação...")
                self.salvar_escalacao_antes_fechamento(rodada_atual)
            
            # Ação 2: Se mercado fechou
            if status_mercado == 4 and not self.mercado_fechado_salvo:
                logger.info("🔒 MERCADO FECHADO - Salvando escalação final")
                self.salvar_escalacao_final(rodada_atual)
                self.mercado_fechado_salvo = True
            
            # Ação 3: Se mercado reabriu (nova rodada)
            if status_mercado == 1 and self.mercado_fechado_salvo:
                logger.info("🔓 MERCADO REABERTO - Nova rodada iniciada")
                self.mercado_fechado_salvo = False
                
                # Coletar pontuações da rodada anterior
                if rodada_atual > 1:
                    logger.info(f"📊 Coletando pontuações da rodada {rodada_atual - 1}")
                    self.coletar_pontuacoes_rodada()
            
            self.ultima_verificacao_mercado = agora
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar mercado: {e}", exc_info=True)
    
    # ==================== SALVAR ESCALAÇÃO ====================
    
    def salvar_escalacao_antes_fechamento(self, rodada: int):
        """
        Salva escalação sugerida 1h antes do fechamento
        """
        try:
            logger.info(f"💾 Gerando e salvando escalações para rodada {rodada}...")
            
            mercado = self.api.get_mercado()
            if not mercado:
                logger.error("❌ Não foi possível obter dados do mercado")
                return
            
            atletas = mercado.get("atletas", [])
            clubes = mercado.get("clubes", {})
            
            # Analisar atletas
            atletas_analisados = []
            for atleta in atletas:
                if atleta.get("status_id") != 7:  # Apenas prováveis
                    continue
                    
                clube_id = atleta.get("clube_id")
                clube_info = clubes.get(str(clube_id), {})
                clube_abrev = clube_info.get("abreviacao", "???")
                
                pos_id = atleta.get("posicao_id", 4)
                pos_map = {1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC"}
                pos_abrev = pos_map.get(pos_id, "MEI")
                
                analise = self.mpv_calculator.analisar_jogador(
                    atleta, clube_abrev=clube_abrev, posicao_abrev=pos_abrev,
                    rodada_atual=rodada
                )
                atletas_analisados.append(analise)
            
            # Gerar times (v7: com rodada_atual)
            logger.info("⚽ Gerando time de valorização...")
            time_val, time_pontos = self.team_selector.gerar_times_rodada(
                atletas_analisados, esquema="4-4-2", rodada_atual=rodada
            )
            
            if time_val:
                # Salvar time de valorização
                logger.info(f"💾 Salvando time VALORIZAÇÃO (C${time_val.custo_total:.1f})")
                self.history.salvar_time_escalado(time_val, rodada, self.team_selector.orcamento)
                
            if time_pontos:
                # Salvar time de pontuação
                logger.info(f"💾 Salvando time PONTUAÇÃO (C${time_pontos.custo_total:.1f})")
                self.history.salvar_time_escalado(time_pontos, rodada, self.team_selector.orcamento)
            
            logger.info("✅ Escalações salvas com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar escalação: {e}", exc_info=True)
    
    def salvar_escalacao_final(self, rodada: int):
        """
        Salva escalação final quando mercado fecha
        (mesmo que anterior, mas marca como 'final')
        """
        # Por enquanto, apenas chama a função anterior
        # Futuramente pode verificar mudanças de última hora
        self.salvar_escalacao_antes_fechamento(rodada)
    
    # ==================== MONITORAMENTO DE ATLETAS ====================
    
    def monitorar_status_atletas(self):
        """
        Monitora mudanças de status dos atletas
        (provável -> dúvida -> suspenso -> contundido)
        """
        try:
            logger.info("👥 Monitorando status dos atletas...")
            
            mercado = self.api.get_mercado()
            if not mercado:
                return
            
            atletas = mercado.get("atletas", [])
            mudancas = []
            
            for atleta in atletas:
                atleta_id = atleta.get("atleta_id")
                status_id = atleta.get("status_id")
                apelido = atleta.get("apelido", "")
                
                # Verificar se houve mudança
                status_anterior = self.status_atletas.get(atleta_id)
                
                if status_anterior and status_anterior != status_id:
                    status_map = {7: "PROVÁVEL", 5: "DÚVIDA", 2: "SUSPENSO", 3: "CONTUNDIDO", 6: "NULO"}
                    status_ant_nome = status_map.get(status_anterior, "?")
                    status_novo_nome = status_map.get(status_id, "?")
                    
                    mudancas.append({
                        "atleta": apelido,
                        "de": status_ant_nome,
                        "para": status_novo_nome
                    })
                
                # Atualizar cache
                self.status_atletas[atleta_id] = status_id
            
            if mudancas:
                logger.warning(f"⚠️  {len(mudancas)} atletas mudaram de status:")
                for m in mudancas[:10]:  # Mostrar até 10
                    logger.warning(f"  - {m['atleta']}: {m['de']} → {m['para']}")
            else:
                logger.info("✅ Nenhuma mudança de status detectada")
                
        except Exception as e:
            logger.error(f"❌ Erro ao monitorar atletas: {e}", exc_info=True)
    
    # ==================== COLETA DE PONTUAÇÕES ====================
    
    def coletar_pontuacoes_rodada(self):
        """
        Coleta pontuações dos atletas após rodada encerrar
        """
        try:
            if not self.rodada_atual:
                return
            
            logger.info(f"📊 Coletando pontuações da rodada {self.rodada_atual}...")
            
            mercado = self.api.get_mercado()
            if not mercado:
                return
            
            atletas = mercado.get("atletas", [])
            
            # Contar quantos já pontuaram
            pontuadores = [a for a in atletas if a.get("pontos_num", 0) != 0]
            
            if pontuadores:
                logger.info(f"✅ {len(pontuadores)} atletas já pontuaram")
                
                # Atualizar pontuações dos times salvos
                # TODO: Implementar atualização no banco
                
            else:
                logger.info("⏳ Rodada ainda não iniciou ou sem pontuações")
                
        except Exception as e:
            logger.error(f"❌ Erro ao coletar pontuações: {e}", exc_info=True)
    
    # ==================== BACKUP ====================
    
    def backup_diario(self):
        """
        Faz backup diário do banco de dados
        """
        try:
            logger.info("💾 Executando backup diário...")
            
            import shutil
            from datetime import datetime
            
            data_dir = Path("data/backups")
            data_dir.mkdir(parents=True, exist_ok=True)
            
            db_file = Path("data/cartola.db")
            if db_file.exists():
                backup_file = data_dir / f"cartola_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_file, backup_file)
                logger.info(f"✅ Backup salvo: {backup_file.name}")
                
                # Manter apenas últimos 7 backups
                backups = sorted(data_dir.glob("cartola_backup_*.db"), reverse=True)
                for old_backup in backups[7:]:
                    old_backup.unlink()
                    logger.info(f"🗑️  Backup antigo removido: {old_backup.name}")
            else:
                logger.warning("⚠️  Banco de dados não encontrado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao fazer backup: {e}", exc_info=True)
    
    # ==================== NOVOS JOBS ====================
    
    def atualizar_dados_mercado(self):
        """
        Atualiza dados completos do mercado (atletas, clubes, partidas)
        Executado a cada 30 minutos para manter cache atualizado
        """
        try:
            logger.info("📊 Atualizando dados do mercado...")
            
            # Forçar refresh do cache
            mercado = self.api.get_mercado()
            if not mercado:
                logger.warning("⚠️  Não foi possível obter dados do mercado")
                return
            
            atletas = mercado.get("atletas", [])
            clubes = mercado.get("clubes", {})
            
            # Estatísticas básicas
            provaveis = sum(1 for a in atletas if a.get("status_id") == 7)
            duvidas = sum(1 for a in atletas if a.get("status_id") == 5)
            suspensos = sum(1 for a in atletas if a.get("status_id") == 2)
            
            logger.info(f"✅ Mercado atualizado: {len(atletas)} atletas")
            logger.info(f"   📍 Prováveis: {provaveis} | Dúvidas: {duvidas} | Suspensos: {suspensos}")
            logger.info(f"   🏟️  Clubes: {len(clubes)}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar mercado: {e}", exc_info=True)
    
    def buscar_noticias_times(self):
        """
        Busca notícias de lesões, suspensões e escalações dos times
        Executado a cada 2 horas
        """
        try:
            logger.info("📰 Buscando notícias dos times...")
            
            # Tentar importar o news_collector se existir
            try:
                from src.scrapers.news_collector import NewsCollector
                collector = NewsCollector()
                
                # Buscar notícias de todos os times
                mercado = self.api.get_mercado()
                if mercado:
                    clubes = mercado.get("clubes", {})
                    
                    total_noticias = 0
                    for clube_id, info in clubes.items():
                        abrev = info.get("abreviacao", "")
                        if abrev:
                            noticias = collector.buscar_noticias_time(abrev)
                            if noticias:
                                total_noticias += len(noticias)
                    
                    logger.info(f"✅ {total_noticias} notícias coletadas")
                    
            except ImportError:
                logger.info("ℹ️  NewsCollector não disponível - usando fonte alternativa")
                
                # Fallback: apenas log
                logger.info("✅ Job de notícias executado (sem coletor ativo)")
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar notícias: {e}", exc_info=True)
    
    def atualizar_classificacao_times(self):
        """
        Atualiza classificação e força dos times
        Busca posição real da tabela e calcula força ponderada
        Executado a cada 1 hora
        """
        try:
            logger.info("📈 Atualizando classificação e força dos times...")
            
            status = self.api.get_status_mercado()
            if not status:
                return
            
            rodada_atual = status.get("rodada_atual", 1)
            
            # Buscar partidas para extrair posições
            partidas_response = self.api.get_partidas(rodada_atual)
            
            if isinstance(partidas_response, dict):
                partidas = partidas_response.get("partidas", [])
            elif isinstance(partidas_response, list):
                partidas = partidas_response
            else:
                partidas = []
            
            if partidas:
                # Extrair posições dos times
                posicoes = {}
                for p in partidas:
                    casa_id = p.get("clube_casa_id")
                    visit_id = p.get("clube_visitante_id")
                    
                    if casa_id and p.get("clube_casa_posicao"):
                        posicoes[casa_id] = p.get("clube_casa_posicao")
                    if visit_id and p.get("clube_visitante_posicao"):
                        posicoes[visit_id] = p.get("clube_visitante_posicao")
                
                logger.info(f"✅ Classificação atualizada: {len(posicoes)} times")
                
                # Log detalhado das posições
                for clube_id, posicao in sorted(posicoes.items(), key=lambda x: x[1]):
                    logger.debug(f"   Time {clube_id}: {posicao}º lugar")
            else:
                logger.info("⏳ Sem partidas disponíveis para atualizar classificação")
                
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar classificação: {e}", exc_info=True)
    
    def limpar_cache_api(self):
        """
        Limpa cache da API para forçar dados frescos
        Executado a cada 15 minutos
        """
        try:
            logger.info("🗑️  Limpando cache da API...")
            
            # Limpar cache interno da API
            if hasattr(self.api, '_cache'):
                self.api._cache.clear()
                logger.info("✅ Cache da API limpo")
            else:
                logger.info("ℹ️  Sem cache para limpar")
                
        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache: {e}", exc_info=True)

    def regenerar_sitemap(self):
        """
        Regenera o sitemap.xml a cada 6 horas.
        Executa generate_sitemap.py do projeto.
        """
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "generate_sitemap.py")],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                logger.info(f"✅ Sitemap regenerado: {result.stdout.strip()}")
            else:
                logger.warning(f"⚠️ Sitemap falhou: {result.stderr.strip()}")
        except Exception as e:
            logger.error(f"❌ Erro ao regenerar sitemap: {e}", exc_info=True)


def main():
    """
    Função principal - mantém o scheduler rodando
    """
    scheduler = CartolaScheduler()
    
    try:
        scheduler.iniciar()
        
        logger.info("⏰ Scheduler rodando em background...")
        logger.info("💡 Pressione Ctrl+C para parar")
        
        # Manter rodando indefinidamente
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("\n⌨️  Interrupção detectada (Ctrl+C)")
        scheduler.parar()
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
        scheduler.parar()


if __name__ == "__main__":
    main()
