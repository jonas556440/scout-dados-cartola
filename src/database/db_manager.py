"""
Gerenciador do banco de dados do Cartola FC 2026
"""
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, func, event
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

# Adicionar path do projeto
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.models import (
    Base, Clube, Posicao, Atleta, Rodada, Partida, 
    Scout, HistoricoPreco, Escalacao, create_tables
)
from config.settings import settings


class DatabaseManager:
    """
    Gerenciador do banco de dados SQLite para o Cartola FC
    
    Responsabilidades:
    - Criar e manter o banco de dados
    - Sincronizar dados da API com o banco local
    - Consultas otimizadas para análise
    - Backup e restauração
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or f"sqlite:///{settings.DATA_DIR}/cartola.db"
        self.engine = create_engine(
            self.database_url,
            echo=False,
            connect_args={"check_same_thread": False},
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Ativar WAL mode para melhor concorrência
        if 'sqlite' in self.database_url:
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()

        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Garante que todas as tabelas existem"""
        create_tables(self.engine)
        self._seed_posicoes()
    
    def _seed_posicoes(self):
        """Insere posições padrão se não existirem"""
        with self.get_session() as session:
            if session.query(Posicao).count() == 0:
                posicoes = [
                    Posicao(id=1, nome="Goleiro", abreviacao="GOL"),
                    Posicao(id=2, nome="Lateral", abreviacao="LAT"),
                    Posicao(id=3, nome="Zagueiro", abreviacao="ZAG"),
                    Posicao(id=4, nome="Meia", abreviacao="MEI"),
                    Posicao(id=5, nome="Atacante", abreviacao="ATA"),
                    Posicao(id=6, nome="Técnico", abreviacao="TEC"),
                ]
                session.add_all(posicoes)
                session.commit()
    
    def get_session(self) -> Session:
        """Retorna uma nova sessão do banco"""
        return self.SessionLocal()
    
    # ==================== CLUBES ====================
    
    def sync_clubes(self, clubes_data: Dict[str, Any]) -> int:
        """
        Sincroniza clubes da API com o banco de dados
        
        Args:
            clubes_data: Dicionário de clubes da API
            
        Returns:
            Número de clubes atualizados/inseridos
        """
        count = 0
        with self.get_session() as session:
            for clube_id_str, clube_info in clubes_data.items():
                clube_id = int(clube_id_str)
                
                clube = session.query(Clube).filter_by(id=clube_id).first()
                
                if clube:
                    # Atualizar existente
                    clube.nome = clube_info.get("nome", clube.nome)
                    clube.abreviacao = clube_info.get("abreviacao", clube.abreviacao)
                    clube.slug = clube_info.get("slug", clube.slug)
                else:
                    # Inserir novo
                    clube = Clube(
                        id=clube_id,
                        nome=clube_info.get("nome", ""),
                        abreviacao=clube_info.get("abreviacao", ""),
                        slug=clube_info.get("slug", ""),
                    )
                    session.add(clube)
                
                count += 1
            
            session.commit()
        
        return count
    
    def get_clube(self, clube_id: int) -> Optional[Clube]:
        """Obtém um clube por ID"""
        with self.get_session() as session:
            return session.query(Clube).filter_by(id=clube_id).first()
    
    def get_todos_clubes(self) -> List[Clube]:
        """Obtém todos os clubes"""
        with self.get_session() as session:
            return session.query(Clube).all()
    
    # ==================== ATLETAS ====================
    
    def sync_atletas(self, atletas_data: List[Dict[str, Any]], rodada_id: int = None) -> int:
        """
        Sincroniza atletas da API com o banco de dados
        
        Args:
            atletas_data: Lista de atletas da API
            rodada_id: ID da rodada (para histórico de preços)
            
        Returns:
            Número de atletas atualizados/inseridos
        """
        count = 0
        with self.get_session() as session:
            for atleta_data in atletas_data:
                atleta_id = atleta_data.get("atleta_id")
                
                if not atleta_id:
                    continue
                
                atleta = session.query(Atleta).filter_by(id=atleta_id).first()
                
                preco_atual = atleta_data.get("preco_num", 0.0)
                media_atual = atleta_data.get("media_num", 0.0)
                
                if atleta:
                    # Atualizar existente
                    atleta.nome = atleta_data.get("nome", atleta.nome)
                    atleta.apelido = atleta_data.get("apelido", atleta.apelido)
                    atleta.slug = atleta_data.get("slug", atleta.slug)
                    atleta.clube_id = atleta_data.get("clube_id")
                    atleta.posicao_id = atleta_data.get("posicao_id")
                    atleta.preco_atual = preco_atual
                    atleta.media_atual = media_atual
                    atleta.pontos_total = atleta_data.get("pontos_num", 0.0)
                    atleta.jogos_num = atleta_data.get("jogos_num", 0)
                    atleta.status_id = atleta_data.get("status_id", 6)
                    atleta.foto_url = atleta_data.get("foto")
                else:
                    # Inserir novo
                    atleta = Atleta(
                        id=atleta_id,
                        nome=atleta_data.get("nome", ""),
                        apelido=atleta_data.get("apelido", ""),
                        slug=atleta_data.get("slug", ""),
                        clube_id=atleta_data.get("clube_id"),
                        posicao_id=atleta_data.get("posicao_id"),
                        preco_atual=preco_atual,
                        media_atual=media_atual,
                        pontos_total=atleta_data.get("pontos_num", 0.0),
                        jogos_num=atleta_data.get("jogos_num", 0),
                        status_id=atleta_data.get("status_id", 6),
                        foto_url=atleta_data.get("foto"),
                    )
                    session.add(atleta)
                
                # Registrar histórico de preços
                if rodada_id:
                    self._registrar_preco(
                        session, atleta_id, rodada_id, 
                        preco_atual, atleta_data.get("variacao_num", 0.0), 
                        media_atual
                    )
                
                count += 1
            
            session.commit()
        
        return count
    
    def _registrar_preco(self, session: Session, atleta_id: int, rodada_id: int, 
                         preco: float, variacao: float, media: float):
        """Registra o preço de um atleta para uma rodada"""
        # Verificar se já existe
        existente = session.query(HistoricoPreco).filter_by(
            atleta_id=atleta_id, rodada_id=rodada_id
        ).first()
        
        if existente:
            existente.preco = preco
            existente.variacao = variacao
            existente.media = media
        else:
            historico = HistoricoPreco(
                atleta_id=atleta_id,
                rodada_id=rodada_id,
                preco=preco,
                variacao=variacao,
                media=media
            )
            session.add(historico)
    
    def get_atleta(self, atleta_id: int) -> Optional[Atleta]:
        """Obtém um atleta por ID"""
        with self.get_session() as session:
            return session.query(Atleta).filter_by(id=atleta_id).first()
    
    def get_atletas_provaveis(self) -> List[Atleta]:
        """Obtém atletas com status 'Provável'"""
        with self.get_session() as session:
            return session.query(Atleta).filter_by(status_id=7).all()
    
    def get_atletas_por_posicao(self, posicao_id: int, apenas_provaveis: bool = True) -> List[Atleta]:
        """Obtém atletas de uma posição específica"""
        with self.get_session() as session:
            query = session.query(Atleta).filter_by(posicao_id=posicao_id)
            if apenas_provaveis:
                query = query.filter_by(status_id=7)
            return query.all()
    
    def get_atletas_baratos(self, preco_maximo: float = 10.0, apenas_provaveis: bool = True) -> List[Atleta]:
        """Obtém atletas abaixo de um preço máximo"""
        with self.get_session() as session:
            query = session.query(Atleta).filter(Atleta.preco_atual <= preco_maximo)
            if apenas_provaveis:
                query = query.filter_by(status_id=7)
            return query.order_by(Atleta.preco_atual.desc()).all()
    
    # ==================== SCOUTS ====================
    
    def sync_scouts(self, pontuados_data: Dict[str, Any], rodada_id: int) -> int:
        """
        Sincroniza scouts/pontuações após a rodada
        
        Args:
            pontuados_data: Dados de pontuação da API
            rodada_id: ID da rodada
            
        Returns:
            Número de scouts registrados
        """
        count = 0
        with self.get_session() as session:
            # Garantir que a rodada existe
            rodada = session.query(Rodada).filter_by(id=rodada_id).first()
            if not rodada:
                rodada = Rodada(id=rodada_id, status="encerrada")
                session.add(rodada)
            
            for atleta_id_str, dados in pontuados_data.items():
                atleta_id = int(atleta_id_str)
                
                # Verificar se atleta existe
                atleta = session.query(Atleta).filter_by(id=atleta_id).first()
                if not atleta:
                    continue
                
                scout_data = dados.get("scout", {})
                pontuacao = dados.get("pontuacao", 0.0)
                
                # Verificar se já existe scout para esta rodada
                scout = session.query(Scout).filter_by(
                    atleta_id=atleta_id, rodada_id=rodada_id
                ).first()
                
                if scout:
                    # Atualizar existente
                    scout.pontuacao = pontuacao
                else:
                    # Criar novo
                    scout = Scout(
                        atleta_id=atleta_id,
                        rodada_id=rodada_id,
                        pontuacao=pontuacao,
                        entrou_em_campo=True,
                        # Scouts positivos
                        gol=scout_data.get("G", 0),
                        assistencia=scout_data.get("A", 0),
                        saldo_gols=scout_data.get("SG", 0),
                        falta_sofrida=scout_data.get("FS", 0),
                        finalizacao_fora=scout_data.get("FF", 0),
                        finalizacao_defendida=scout_data.get("FD", 0),
                        finalizacao_trave=scout_data.get("FT", 0),
                        desarme=scout_data.get("DS", 0),
                        roubada_bola=scout_data.get("RB", 0),
                        defesa_dificil=scout_data.get("DD", 0),
                        defesa_penalti=scout_data.get("DP", 0),
                        # Scouts negativos
                        cartao_amarelo=scout_data.get("CA", 0),
                        cartao_vermelho=scout_data.get("CV", 0),
                        gol_contra=scout_data.get("GC", 0),
                        penalti_perdido=scout_data.get("PP", 0),
                        penalti_cometido=scout_data.get("PC", 0),
                        falta_cometida=scout_data.get("FC", 0),
                        gol_sofrido=scout_data.get("GS", 0),
                        impedimento=scout_data.get("I", 0),
                        passe_incompleto=scout_data.get("PI", 0),
                    )
                    session.add(scout)
                
                count += 1
            
            session.commit()
        
        return count
    
    def get_scouts_atleta(self, atleta_id: int, ultimas_n: int = None) -> List[Scout]:
        """Obtém histórico de scouts de um atleta"""
        with self.get_session() as session:
            query = session.query(Scout).filter_by(atleta_id=atleta_id)\
                .order_by(Scout.rodada_id.desc())
            
            if ultimas_n:
                query = query.limit(ultimas_n)
            
            return query.all()
    
    def get_media_pontos_atleta(self, atleta_id: int, ultimas_n: int = 5) -> float:
        """Calcula média de pontos de um atleta nas últimas N rodadas"""
        with self.get_session() as session:
            result = session.query(func.avg(Scout.pontuacao))\
                .filter_by(atleta_id=atleta_id)\
                .filter(Scout.entrou_em_campo == True)\
                .order_by(Scout.rodada_id.desc())\
                .limit(ultimas_n)\
                .scalar()
            
            return result or 0.0
    
    # ==================== RODADAS ====================
    
    def get_ou_criar_rodada(self, rodada_id: int) -> Rodada:
        """Obtém ou cria uma rodada"""
        with self.get_session() as session:
            rodada = session.query(Rodada).filter_by(id=rodada_id).first()
            
            if not rodada:
                rodada = Rodada(id=rodada_id, status="aberta")
                session.add(rodada)
                session.commit()
            
            return rodada
    
    def atualizar_status_rodada(self, rodada_id: int, status: str):
        """Atualiza o status de uma rodada"""
        with self.get_session() as session:
            rodada = session.query(Rodada).filter_by(id=rodada_id).first()
            if rodada:
                rodada.status = status
                session.commit()
    
    # ==================== ESCALAÇÕES ====================
    
    def salvar_escalacao(self, rodada_id: int, tipo: str, esquema: str,
                         atletas_ids: List[int], capitao_id: int,
                         custo_total: float, pontuacao_prevista: float = 0.0) -> Escalacao:
        """
        Salva uma escalação gerada
        
        Args:
            rodada_id: ID da rodada
            tipo: 'valorizacao' ou 'pontuacao'
            esquema: Esquema tático (ex: '4-4-2')
            atletas_ids: Lista de IDs dos atletas
            capitao_id: ID do capitão
            custo_total: Custo total da escalação
            pontuacao_prevista: Pontuação estimada
        """
        with self.get_session() as session:
            escalacao = Escalacao(
                rodada_id=rodada_id,
                tipo=tipo,
                esquema=esquema,
                atletas_ids=atletas_ids,
                capitao_id=capitao_id,
                custo_total=custo_total,
                pontuacao_prevista=pontuacao_prevista
            )
            session.add(escalacao)
            session.commit()
            return escalacao
    
    def get_escalacoes_rodada(self, rodada_id: int) -> List[Escalacao]:
        """Obtém escalações de uma rodada"""
        with self.get_session() as session:
            return session.query(Escalacao).filter_by(rodada_id=rodada_id).all()
    
    # ==================== ESTATÍSTICAS ====================
    
    def get_estatisticas_gerais(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais do banco"""
        with self.get_session() as session:
            return {
                "total_atletas": session.query(Atleta).count(),
                "atletas_provaveis": session.query(Atleta).filter_by(status_id=7).count(),
                "total_clubes": session.query(Clube).count(),
                "total_scouts": session.query(Scout).count(),
                "total_escalacoes": session.query(Escalacao).count(),
            }
    
    def get_top_pontuadores(self, posicao_id: int = None, limite: int = 10) -> List[Atleta]:
        """Obtém os atletas com maior pontuação total"""
        with self.get_session() as session:
            query = session.query(Atleta).filter(Atleta.pontos_total > 0)
            
            if posicao_id:
                query = query.filter_by(posicao_id=posicao_id)
            
            return query.order_by(Atleta.pontos_total.desc()).limit(limite).all()
    
    def get_melhores_custo_beneficio(self, preco_maximo: float = 10.0, 
                                      posicao_id: int = None, limite: int = 10) -> List[Dict[str, Any]]:
        """Obtém atletas com melhor custo-benefício"""
        with self.get_session() as session:
            query = session.query(Atleta).filter(
                Atleta.preco_atual <= preco_maximo,
                Atleta.preco_atual > 0,
                Atleta.status_id == 7
            )
            
            if posicao_id:
                query = query.filter_by(posicao_id=posicao_id)
            
            atletas = query.all()
            
            # Calcular custo-benefício
            resultados = []
            for atleta in atletas:
                cb = atleta.media_atual / atleta.preco_atual if atleta.preco_atual > 0 else 0
                resultados.append({
                    "atleta": atleta,
                    "custo_beneficio": cb
                })
            
            # Ordenar por custo-benefício
            resultados.sort(key=lambda x: x["custo_beneficio"], reverse=True)
            
            return resultados[:limite]


# Instância global do gerenciador
db_manager = DatabaseManager()


if __name__ == "__main__":
    # Teste do gerenciador
    print("🗄️ Testando DatabaseManager...")
    
    manager = DatabaseManager()
    stats = manager.get_estatisticas_gerais()
    
    print(f"📊 Estatísticas do banco:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
