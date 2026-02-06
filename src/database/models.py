"""
Modelos do banco de dados para o Cartola FC 2026
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Boolean, 
    DateTime, ForeignKey, Text, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class Clube(Base):
    """Modelo para clubes do Brasileirão"""
    __tablename__ = "clubes"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    abreviacao = Column(String(10), nullable=False)
    slug = Column(String(50))
    escudo_url = Column(String(500))
    
    # Relacionamentos
    atletas = relationship("Atleta", back_populates="clube")
    partidas_mandante = relationship("Partida", foreign_keys="Partida.clube_mandante_id", back_populates="clube_mandante")
    partidas_visitante = relationship("Partida", foreign_keys="Partida.clube_visitante_id", back_populates="clube_visitante")
    
    def __repr__(self):
        return f"<Clube(id={self.id}, nome='{self.nome}')>"


class Posicao(Base):
    """Modelo para posições dos jogadores"""
    __tablename__ = "posicoes"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(50), nullable=False)
    abreviacao = Column(String(10), nullable=False)
    
    # Relacionamentos
    atletas = relationship("Atleta", back_populates="posicao")
    
    def __repr__(self):
        return f"<Posicao(id={self.id}, nome='{self.nome}')>"


class Atleta(Base):
    """Modelo para atletas/jogadores"""
    __tablename__ = "atletas"
    
    id = Column(Integer, primary_key=True)  # atleta_id da API
    nome = Column(String(200), nullable=False)
    apelido = Column(String(100), nullable=False)
    slug = Column(String(100))
    foto_url = Column(String(500))
    
    # Chaves estrangeiras
    clube_id = Column(Integer, ForeignKey("clubes.id"))
    posicao_id = Column(Integer, ForeignKey("posicoes.id"))
    
    # Dados atuais
    preco_atual = Column(Float, default=0.0)
    media_atual = Column(Float, default=0.0)
    pontos_total = Column(Float, default=0.0)
    jogos_num = Column(Integer, default=0)
    status_id = Column(Integer, default=6)  # 7 = Provável, 6 = Nulo, etc.
    
    # Metadados
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    clube = relationship("Clube", back_populates="atletas")
    posicao = relationship("Posicao", back_populates="atletas")
    historico_precos = relationship("HistoricoPreco", back_populates="atleta", order_by="HistoricoPreco.rodada_id")
    scouts = relationship("Scout", back_populates="atleta", order_by="Scout.rodada_id")
    
    # Índices
    __table_args__ = (
        Index('idx_atleta_clube', 'clube_id'),
        Index('idx_atleta_posicao', 'posicao_id'),
        Index('idx_atleta_status', 'status_id'),
        Index('idx_atleta_preco', 'preco_atual'),
    )
    
    def __repr__(self):
        return f"<Atleta(id={self.id}, apelido='{self.apelido}', preco={self.preco_atual})>"
    
    @property
    def custo_beneficio(self) -> float:
        """Calcula o custo-benefício (média / preço)"""
        if self.preco_atual and self.preco_atual > 0:
            return self.media_atual / self.preco_atual
        return 0.0


class Rodada(Base):
    """Modelo para rodadas do campeonato"""
    __tablename__ = "rodadas"
    
    id = Column(Integer, primary_key=True)
    inicio = Column(DateTime)
    fim = Column(DateTime)
    status = Column(String(20))  # 'aberta', 'fechada', 'encerrada'
    
    # Relacionamentos
    partidas = relationship("Partida", back_populates="rodada")
    scouts = relationship("Scout", back_populates="rodada")
    historico_precos = relationship("HistoricoPreco", back_populates="rodada")
    escalacoes = relationship("Escalacao", back_populates="rodada")
    
    def __repr__(self):
        return f"<Rodada(id={self.id}, status='{self.status}')>"


class Partida(Base):
    """Modelo para partidas/jogos"""
    __tablename__ = "partidas"
    
    id = Column(Integer, primary_key=True)
    rodada_id = Column(Integer, ForeignKey("rodadas.id"))
    clube_mandante_id = Column(Integer, ForeignKey("clubes.id"))
    clube_visitante_id = Column(Integer, ForeignKey("clubes.id"))
    
    # Resultado
    placar_mandante = Column(Integer)
    placar_visitante = Column(Integer)
    
    # Metadados
    data_hora = Column(DateTime)
    local = Column(String(200))
    transmissao = Column(Boolean, default=False)
    
    # Relacionamentos
    rodada = relationship("Rodada", back_populates="partidas")
    clube_mandante = relationship("Clube", foreign_keys=[clube_mandante_id], back_populates="partidas_mandante")
    clube_visitante = relationship("Clube", foreign_keys=[clube_visitante_id], back_populates="partidas_visitante")
    
    # Índices
    __table_args__ = (
        Index('idx_partida_rodada', 'rodada_id'),
    )
    
    def __repr__(self):
        return f"<Partida(id={self.id}, rodada={self.rodada_id})>"


class Scout(Base):
    """Modelo para scouts/estatísticas por rodada"""
    __tablename__ = "scouts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"), nullable=False)
    rodada_id = Column(Integer, ForeignKey("rodadas.id"), nullable=False)
    
    # Pontuação
    pontuacao = Column(Float, default=0.0)
    
    # Scouts positivos
    gol = Column(Integer, default=0)              # G
    assistencia = Column(Integer, default=0)       # A
    saldo_gols = Column(Integer, default=0)        # SG
    falta_sofrida = Column(Integer, default=0)     # FS
    finalizacao_fora = Column(Integer, default=0)  # FF
    finalizacao_defendida = Column(Integer, default=0)  # FD
    finalizacao_trave = Column(Integer, default=0) # FT
    desarme = Column(Integer, default=0)           # DS
    roubada_bola = Column(Integer, default=0)      # RB
    defesa_dificil = Column(Integer, default=0)    # DD
    defesa_penalti = Column(Integer, default=0)    # DP
    
    # Scouts negativos
    cartao_amarelo = Column(Integer, default=0)    # CA
    cartao_vermelho = Column(Integer, default=0)   # CV
    gol_contra = Column(Integer, default=0)        # GC
    penalti_perdido = Column(Integer, default=0)   # PP
    penalti_cometido = Column(Integer, default=0)  # PC
    falta_cometida = Column(Integer, default=0)    # FC
    gol_sofrido = Column(Integer, default=0)       # GS
    impedimento = Column(Integer, default=0)       # I
    passe_incompleto = Column(Integer, default=0)  # PI
    
    # Metadados
    entrou_em_campo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    atleta = relationship("Atleta", back_populates="scouts")
    rodada = relationship("Rodada", back_populates="scouts")
    
    # Constraints e índices
    __table_args__ = (
        UniqueConstraint('atleta_id', 'rodada_id', name='uq_scout_atleta_rodada'),
        Index('idx_scout_atleta', 'atleta_id'),
        Index('idx_scout_rodada', 'rodada_id'),
        Index('idx_scout_pontuacao', 'pontuacao'),
    )
    
    def __repr__(self):
        return f"<Scout(atleta_id={self.atleta_id}, rodada={self.rodada_id}, pts={self.pontuacao})>"


class HistoricoPreco(Base):
    """Modelo para histórico de preços dos atletas"""
    __tablename__ = "historico_precos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"), nullable=False)
    rodada_id = Column(Integer, ForeignKey("rodadas.id"), nullable=False)
    
    preco = Column(Float, nullable=False)
    variacao = Column(Float, default=0.0)
    media = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    atleta = relationship("Atleta", back_populates="historico_precos")
    rodada = relationship("Rodada", back_populates="historico_precos")
    
    # Constraints e índices
    __table_args__ = (
        UniqueConstraint('atleta_id', 'rodada_id', name='uq_preco_atleta_rodada'),
        Index('idx_preco_atleta', 'atleta_id'),
        Index('idx_preco_rodada', 'rodada_id'),
    )
    
    def __repr__(self):
        return f"<HistoricoPreco(atleta={self.atleta_id}, rodada={self.rodada_id}, preco={self.preco})>"


class Escalacao(Base):
    """Modelo para escalações geradas pelo sistema"""
    __tablename__ = "escalacoes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rodada_id = Column(Integer, ForeignKey("rodadas.id"), nullable=False)
    
    tipo = Column(String(20), nullable=False)  # 'valorizacao' ou 'pontuacao'
    esquema = Column(String(10), nullable=False)  # Ex: '4-4-2'
    
    # Atletas escalados (JSON com IDs e capitão)
    atletas_ids = Column(JSON, nullable=False)
    capitao_id = Column(Integer)
    
    # Custos e previsões
    custo_total = Column(Float, default=0.0)
    pontuacao_prevista = Column(Float, default=0.0)
    pontuacao_real = Column(Float)  # Preenchido após a rodada
    
    # Metadados
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    rodada = relationship("Rodada", back_populates="escalacoes")
    
    # Índices
    __table_args__ = (
        Index('idx_escalacao_rodada', 'rodada_id'),
        Index('idx_escalacao_tipo', 'tipo'),
    )
    
    def __repr__(self):
        return f"<Escalacao(rodada={self.rodada_id}, tipo='{self.tipo}')>"


class ConfiguracaoEscalacao(Base):
    """Modelo para configurações de escalação"""
    __tablename__ = "configuracoes_escalacao"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    tipo = Column(String(20), nullable=False)  # 'valorizacao' ou 'pontuacao'
    
    # Configurações JSON
    parametros = Column(JSON, default={})
    
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ConfiguracaoEscalacao(nome='{self.nome}', tipo='{self.tipo}')>"


class TimeHistorico(Base):
    """
    Histórico de times escalados com resultados
    Cada registro representa um time escalado em uma rodada
    """
    __tablename__ = "times_historico"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rodada_id = Column(Integer, ForeignKey("rodadas.id"), nullable=False)
    
    # Tipo e esquema
    tipo = Column(String(20), nullable=False)  # 'valorizacao' ou 'pontuacao'
    esquema = Column(String(10), nullable=False)  # Ex: '4-4-2'
    
    # Atletas escalados (JSON completo com dados)
    titulares = Column(JSON, nullable=False)  # Lista de {atleta_id, nome, posicao, preco_escalado, ...}
    reservas = Column(JSON)  # Lista de reservas
    capitao_id = Column(Integer, nullable=False)
    
    # Custos
    custo_total = Column(Float, default=0.0)
    cartoletas_inicial = Column(Float, default=100.0)  # Cartoletas no início da rodada
    cartoletas_restante = Column(Float, default=0.0)  # Cartoletas não usadas
    
    # Pontuações
    pontuacao_prevista = Column(Float, default=0.0)
    pontuacao_real = Column(Float)  # Preenchido após rodada encerrar
    pontuacao_capitao = Column(Float)  # Pontos extras do capitão
    
    # Valorização
    valorizacao_prevista = Column(Float, default=0.0)
    valorizacao_real = Column(Float)  # Quanto valorizou realmente
    
    # Status
    resultado_registrado = Column(Boolean, default=False)
    
    # Metadados
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    rodada = relationship("Rodada")
    
    # Índices
    __table_args__ = (
        Index('idx_time_hist_rodada', 'rodada_id'),
        Index('idx_time_hist_tipo', 'tipo'),
        UniqueConstraint('rodada_id', 'tipo', name='uq_time_rodada_tipo'),
    )
    
    def __repr__(self):
        return f"<TimeHistorico(rodada={self.rodada_id}, tipo='{self.tipo}', pts_real={self.pontuacao_real})>"


class PatrimonioEvolucao(Base):
    """
    Evolução do patrimônio (cartoletas) ao longo das rodadas
    Rastreia ganhos e perdas por valorização dos jogadores
    """
    __tablename__ = "patrimonio_evolucao"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rodada_id = Column(Integer, ForeignKey("rodadas.id"), nullable=False)
    
    # Tipo de time (cada um tem patrimônio separado)
    tipo = Column(String(20), nullable=False)  # 'valorizacao' ou 'pontuacao'
    
    # Patrimônio
    cartoletas_inicio = Column(Float, default=100.0)  # Cartoletas no início da rodada
    cartoletas_fim = Column(Float, default=100.0)     # Cartoletas após valorização
    
    # Detalhes da rodada
    custo_time = Column(Float, default=0.0)  # Quanto gastou no time
    cartoletas_em_caixa = Column(Float, default=0.0)  # Cartoletas não usadas (reservadas)
    valorizacao_obtida = Column(Float, default=0.0)  # Quanto ganhou/perdeu com valorização
    
    # Pontuação
    pontuacao_rodada = Column(Float, default=0.0)
    pontuacao_acumulada = Column(Float, default=0.0)
    
    # Rankings
    ranking_rodada = Column(Integer)  # Posição no ranking da rodada
    ranking_geral = Column(Integer)   # Posição no ranking geral
    
    # Metadados
    created_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    rodada = relationship("Rodada")
    
    # Índices
    __table_args__ = (
        Index('idx_patrim_rodada', 'rodada_id'),
        Index('idx_patrim_tipo', 'tipo'),
        UniqueConstraint('rodada_id', 'tipo', name='uq_patrimonio_rodada_tipo'),
    )
    
    def __repr__(self):
        return f"<PatrimonioEvolucao(rodada={self.rodada_id}, tipo='{self.tipo}', cartoletas={self.cartoletas_fim})>"


class EstatisticasExternas(Base):
    """
    Estatísticas externas de jogadores (FBref, Sofascore, etc.)
    Complementa os dados do Cartola com métricas avançadas
    """
    __tablename__ = "estatisticas_externas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    atleta_id = Column(Integer, ForeignKey("atletas.id"), nullable=False)
    
    # Fonte dos dados
    fonte = Column(String(50), nullable=False)  # 'fbref', 'sofascore', 'footstats', etc.
    
    # Estatísticas avançadas
    xg = Column(Float)               # Expected Goals
    xa = Column(Float)               # Expected Assists
    xg_per_90 = Column(Float)        # xG por 90 minutos
    shots_per_90 = Column(Float)     # Finalizações por 90 min
    key_passes_per_90 = Column(Float)  # Passes decisivos por 90 min
    
    # Estatísticas defensivas
    tackles_per_90 = Column(Float)   # Desarmes por 90 min
    interceptions_per_90 = Column(Float)  # Interceptações por 90 min
    blocks_per_90 = Column(Float)    # Bloqueios por 90 min
    
    # Estatísticas de goleiro
    saves_per_90 = Column(Float)     # Defesas por 90 min
    save_pct = Column(Float)         # % de defesas
    clean_sheet_pct = Column(Float)  # % de jogos sem sofrer gol
    
    # Métricas calculadas
    score_potencial = Column(Float)  # Score de potencial (0-100)
    score_forma = Column(Float)      # Score de forma atual (0-100)
    tendencia = Column(String(20))   # 'subindo', 'estavel', 'caindo'
    
    # JSON para dados extras
    dados_extras = Column(JSON)
    
    # Metadados
    temporada = Column(String(10))   # Ex: '2026'
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    atleta = relationship("Atleta")
    
    # Índices
    __table_args__ = (
        Index('idx_estat_atleta', 'atleta_id'),
        Index('idx_estat_fonte', 'fonte'),
        UniqueConstraint('atleta_id', 'fonte', 'temporada', name='uq_estat_atleta_fonte_temp'),
    )
    
    def __repr__(self):
        return f"<EstatisticasExternas(atleta_id={self.atleta_id}, fonte='{self.fonte}')>"


# Função para criar todas as tabelas
def create_tables(engine):
    """Cria todas as tabelas no banco de dados"""
    Base.metadata.create_all(engine)


# Função para obter uma sessão
def get_session(database_url: str = "sqlite:///data/cartola.db"):
    """Retorna uma sessão do banco de dados"""
    engine = create_engine(database_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()
