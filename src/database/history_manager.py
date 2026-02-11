"""
History Manager - Gerenciador de Histórico de Times e Patrimônio
Cartola FC 2026

Responsável por:
- Salvar times escalados a cada rodada
- Registrar resultados após rodada encerrar
- Calcular evolução de patrimônio (cartoletas)
- Fornecer dados históricos para análises
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, Session

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings
from src.database.models import (
    Base, Rodada, Atleta, Scout, TimeHistorico, 
    PatrimonioEvolucao, EstatisticasExternas
)
from src.analysis.team_selector import TimeEscalado


class HistoryManager:
    """
    Gerenciador de histórico de escalações e patrimônio
    
    Fluxo típico:
    1. escalar_time() - Gera e salva time para a rodada
    2. (após rodada encerrar) registrar_resultado() - Registra pontuação real
    3. calcular_patrimonio() - Atualiza cartoletas com base na valorização
    """
    
    CARTOLETAS_INICIAL = 100.0
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Retorna uma nova sessão do banco"""
        return self.SessionLocal()

    from contextlib import contextmanager

    @contextmanager
    def session_scope(self):
        """Context manager para sessões com commit/rollback automático.
        
        Uso:
            with history.session_scope() as session:
                session.query(...).
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ==================== SALVAR TIME ====================
    
    def salvar_time_escalado(
        self,
        time: TimeEscalado,
        rodada_id: int,
        cartoletas_disponiveis: float = None
    ) -> TimeHistorico:
        """
        Salva um time escalado no histórico
        
        Args:
            time: TimeEscalado gerado pelo TeamSelector
            rodada_id: ID da rodada
            cartoletas_disponiveis: Cartoletas disponíveis (ou calcula do histórico)
            
        Returns:
            TimeHistorico salvo no banco
        """
        session = self.get_session()
        
        try:
            # Calcular cartoletas disponíveis se não informado
            if cartoletas_disponiveis is None:
                cartoletas_disponiveis = self.get_cartoletas_atuais(time.tipo, session)
            
            # Verificar se já existe time desse tipo para esta rodada
            existente = session.query(TimeHistorico).filter_by(
                rodada_id=rodada_id,
                tipo=time.tipo
            ).first()
            
            if existente:
                # Atualizar existente
                historico = existente
            else:
                # Criar novo
                historico = TimeHistorico()
            
            # Converter titulares para JSON
            titulares_json = [
                {
                    "atleta_id": t.atleta_id,
                    "apelido": t.apelido,
                    "posicao_abrev": t.posicao_abrev,
                    "clube_abrev": t.clube_abrev,
                    "preco": t.preco,
                    "media": t.media,
                    "pontuacao_esperada": t.pontuacao_esperada,
                }
                for t in time.titulares
            ]
            
            # Converter reservas para JSON
            reservas_json = [
                {
                    "atleta_id": r.atleta_id,
                    "apelido": r.apelido,
                    "posicao_abrev": r.posicao_abrev,
                    "clube_abrev": r.clube_abrev,
                    "preco": r.preco,
                }
                for r in time.reservas
            ] if time.reservas else []
            
            # Preencher dados
            historico.rodada_id = rodada_id
            historico.tipo = time.tipo
            historico.esquema = time.esquema
            historico.titulares = titulares_json
            historico.reservas = reservas_json
            historico.capitao_id = time.capitao.atleta_id
            historico.custo_total = time.custo_total
            historico.cartoletas_inicial = cartoletas_disponiveis
            historico.cartoletas_restante = cartoletas_disponiveis - time.custo_total
            historico.pontuacao_prevista = time.pontuacao_prevista
            historico.valorizacao_prevista = time.valorizacao_esperada
            historico.resultado_registrado = False
            historico.updated_at = datetime.now()
            
            if not existente:
                session.add(historico)
            
            session.commit()
            session.refresh(historico)
            
            return historico
            
        finally:
            session.close()
    
    # ==================== REGISTRAR RESULTADO ====================
    
    def registrar_resultado_rodada(
        self,
        rodada_id: int,
        pontuacoes_atletas: Dict[int, float] = None
    ) -> Dict[str, Any]:
        """
        Registra o resultado de uma rodada após ela encerrar
        
        Args:
            rodada_id: ID da rodada
            pontuacoes_atletas: Dict {atleta_id: pontuacao_real} (se None, busca da API)
            
        Returns:
            Dict com resultados de ambos os times
        """
        session = self.get_session()
        
        try:
            resultados = {}
            
            # Buscar times escalados para esta rodada
            times = session.query(TimeHistorico).filter_by(
                rodada_id=rodada_id
            ).all()
            
            if not times:
                return {"erro": "Nenhum time escalado para esta rodada"}
            
            # Se não passou pontuações, buscar dos scouts no banco
            if pontuacoes_atletas is None:
                pontuacoes_atletas = {}
                scouts = session.query(Scout).filter_by(rodada_id=rodada_id).all()
                for scout in scouts:
                    pontuacoes_atletas[scout.atleta_id] = scout.pontuacao
            
            for time_hist in times:
                # Calcular pontuação real
                pontuacao_real = 0.0
                pontuacao_capitao = 0.0
                
                for titular in time_hist.titulares:
                    atleta_id = titular["atleta_id"]
                    pts = pontuacoes_atletas.get(atleta_id, 0.0)
                    
                    if atleta_id == time_hist.capitao_id:
                        # Capitão pontua 1.5x
                        pontuacao_capitao = pts * 0.5  # Bônus extra
                        pts *= 1.5
                    
                    pontuacao_real += pts
                
                # Atualizar registro
                time_hist.pontuacao_real = round(pontuacao_real, 2)
                time_hist.pontuacao_capitao = round(pontuacao_capitao, 2)
                time_hist.resultado_registrado = True
                time_hist.updated_at = datetime.now()
                
                resultados[time_hist.tipo] = {
                    "pontuacao_prevista": time_hist.pontuacao_prevista,
                    "pontuacao_real": time_hist.pontuacao_real,
                    "diferenca": round(time_hist.pontuacao_real - time_hist.pontuacao_prevista, 2),
                }
            
            session.commit()
            
            # Atualizar patrimônio
            for time_hist in times:
                self._atualizar_patrimonio(session, time_hist)
            
            session.commit()
            
            return resultados
            
        finally:
            session.close()
    
    def _atualizar_patrimonio(self, session: Session, time_hist: TimeHistorico):
        """Atualiza o patrimônio após uma rodada"""
        # Buscar patrimônio anterior
        patrimonio_anterior = session.query(PatrimonioEvolucao).filter(
            PatrimonioEvolucao.tipo == time_hist.tipo,
            PatrimonioEvolucao.rodada_id < time_hist.rodada_id
        ).order_by(desc(PatrimonioEvolucao.rodada_id)).first()
        
        if patrimonio_anterior:
            cartoletas_inicio = patrimonio_anterior.cartoletas_fim
            pontuacao_acumulada = patrimonio_anterior.pontuacao_acumulada
        else:
            cartoletas_inicio = self.CARTOLETAS_INICIAL
            pontuacao_acumulada = 0.0
        
        # Calcular valorização real
        valorizacao_real = self._calcular_valorizacao_real(session, time_hist)
        
        # Novo patrimônio = cartoletas em caixa + valor do time + valorização
        cartoletas_em_caixa = time_hist.cartoletas_restante
        valor_time = time_hist.custo_total  # Valor que pagou pelos jogadores
        cartoletas_fim = cartoletas_em_caixa + valor_time + valorizacao_real
        
        # Atualizar time histórico
        time_hist.valorizacao_real = valorizacao_real
        
        # Criar ou atualizar patrimônio
        patrimonio = session.query(PatrimonioEvolucao).filter_by(
            rodada_id=time_hist.rodada_id,
            tipo=time_hist.tipo
        ).first()
        
        if not patrimonio:
            patrimonio = PatrimonioEvolucao()
            session.add(patrimonio)
        
        patrimonio.rodada_id = time_hist.rodada_id
        patrimonio.tipo = time_hist.tipo
        patrimonio.cartoletas_inicio = cartoletas_inicio
        patrimonio.cartoletas_fim = round(cartoletas_fim, 2)
        patrimonio.custo_time = time_hist.custo_total
        patrimonio.cartoletas_em_caixa = cartoletas_em_caixa
        patrimonio.valorizacao_obtida = round(valorizacao_real, 2)
        patrimonio.pontuacao_rodada = time_hist.pontuacao_real or 0.0
        patrimonio.pontuacao_acumulada = round(
            pontuacao_acumulada + (time_hist.pontuacao_real or 0.0), 2
        )
    
    def _calcular_valorizacao_real(
        self, session: Session, time_hist: TimeHistorico
    ) -> float:
        """
        Calcula a valorização real dos jogadores do time
        Compara preço atual com preço quando escalou
        """
        valorizacao = 0.0
        
        for titular in time_hist.titulares:
            atleta_id = titular["atleta_id"]
            preco_escalado = titular["preco"]
            
            # Buscar preço atual do atleta
            atleta = session.query(Atleta).filter_by(id=atleta_id).first()
            if atleta:
                preco_atual = atleta.preco_atual
                valorizacao += (preco_atual - preco_escalado)
        
        return valorizacao
    
    # ==================== CONSULTAS ====================
    
    def get_cartoletas_atuais(self, tipo: str, session: Session = None) -> float:
        """
        Retorna cartoletas disponíveis para um tipo de time
        
        Args:
            tipo: 'valorizacao' ou 'pontuacao'
            session: Sessão do banco (opcional)
            
        Returns:
            Cartoletas disponíveis
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            # Buscar último patrimônio
            ultimo = session.query(PatrimonioEvolucao).filter_by(
                tipo=tipo
            ).order_by(desc(PatrimonioEvolucao.rodada_id)).first()
            
            if ultimo:
                return ultimo.cartoletas_fim
            
            return self.CARTOLETAS_INICIAL
            
        finally:
            if close_session:
                session.close()
    
    def get_historico_times(
        self, 
        tipo: str = None, 
        limit: int = 10
    ) -> List[TimeHistorico]:
        """
        Retorna histórico de times escalados
        
        Args:
            tipo: Filtrar por tipo ('valorizacao' ou 'pontuacao')
            limit: Limite de resultados
            
        Returns:
            Lista de TimeHistorico
        """
        session = self.get_session()
        
        try:
            query = session.query(TimeHistorico)
            
            if tipo:
                query = query.filter_by(tipo=tipo)
            
            return query.order_by(desc(TimeHistorico.rodada_id)).limit(limit).all()
            
        finally:
            session.close()
    
    def get_evolucao_patrimonio(
        self, 
        tipo: str = None
    ) -> List[PatrimonioEvolucao]:
        """
        Retorna evolução do patrimônio ao longo das rodadas
        
        Args:
            tipo: Filtrar por tipo
            
        Returns:
            Lista de PatrimonioEvolucao ordenada por rodada
        """
        session = self.get_session()
        
        try:
            query = session.query(PatrimonioEvolucao)
            
            if tipo:
                query = query.filter_by(tipo=tipo)
            
            return query.order_by(PatrimonioEvolucao.rodada_id).all()
            
        finally:
            session.close()
    
    def get_resumo_geral(self) -> Dict[str, Any]:
        """
        Retorna resumo geral de ambos os times
        
        Returns:
            Dict com estatísticas consolidadas
        """
        session = self.get_session()
        
        try:
            resumo = {}
            
            for tipo in ["valorizacao", "pontuacao"]:
                # Último patrimônio
                ultimo_patrim = session.query(PatrimonioEvolucao).filter_by(
                    tipo=tipo
                ).order_by(desc(PatrimonioEvolucao.rodada_id)).first()
                
                # Estatísticas de times
                stats = session.query(
                    func.count(TimeHistorico.id).label("total_rodadas"),
                    func.sum(TimeHistorico.pontuacao_real).label("pontuacao_total"),
                    func.avg(TimeHistorico.pontuacao_real).label("media_pontuacao"),
                    func.max(TimeHistorico.pontuacao_real).label("maior_pontuacao"),
                    func.min(TimeHistorico.pontuacao_real).label("menor_pontuacao"),
                ).filter(
                    TimeHistorico.tipo == tipo,
                    TimeHistorico.resultado_registrado == True
                ).first()
                
                resumo[tipo] = {
                    "cartoletas_atuais": ultimo_patrim.cartoletas_fim if ultimo_patrim else 100.0,
                    "cartoletas_iniciais": 100.0,
                    "lucro_total": (ultimo_patrim.cartoletas_fim - 100.0) if ultimo_patrim else 0.0,
                    "rodadas_jogadas": stats.total_rodadas or 0,
                    "pontuacao_total": stats.pontuacao_total or 0.0,
                    "media_pontuacao": round(stats.media_pontuacao or 0.0, 2),
                    "maior_pontuacao": stats.maior_pontuacao or 0.0,
                    "menor_pontuacao": stats.menor_pontuacao or 0.0,
                }
            
            return resumo
            
        finally:
            session.close()
    
    def get_melhores_jogadores(
        self, 
        rodadas: int = 5, 
        posicao: str = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna os melhores jogadores das últimas N rodadas
        
        Args:
            rodadas: Quantas rodadas considerar
            posicao: Filtrar por posição
            
        Returns:
            Lista de jogadores com estatísticas
        """
        session = self.get_session()
        
        try:
            # Buscar últimas rodadas com scouts
            ultima_rodada = session.query(func.max(Scout.rodada_id)).scalar() or 0
            rodada_inicial = max(1, ultima_rodada - rodadas + 1)
            
            # Agregação de scouts
            query = session.query(
                Scout.atleta_id,
                Atleta.apelido,
                Atleta.preco_atual,
                func.count(Scout.id).label("jogos"),
                func.sum(Scout.pontuacao).label("pontuacao_total"),
                func.avg(Scout.pontuacao).label("media"),
            ).join(
                Atleta, Scout.atleta_id == Atleta.id
            ).filter(
                Scout.rodada_id >= rodada_inicial,
                Scout.entrou_em_campo == True
            ).group_by(
                Scout.atleta_id, Atleta.apelido, Atleta.preco_atual
            ).order_by(
                desc("media")
            ).limit(50)
            
            resultados = []
            for row in query.all():
                resultados.append({
                    "atleta_id": row.atleta_id,
                    "apelido": row.apelido,
                    "preco": row.preco_atual,
                    "jogos": row.jogos,
                    "pontuacao_total": round(row.pontuacao_total, 2),
                    "media": round(row.media, 2),
                    "custo_beneficio": round(row.media / row.preco_atual, 2) if row.preco_atual > 0 else 0,
                })
            
            return resultados
            
        finally:
            session.close()


# Instância global
history_manager = HistoryManager()
