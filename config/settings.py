"""
Configurações do sistema Cartola FC 2026
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configurações gerais do sistema"""
    
    # Diretórios
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    BACKUP_DIR: Path = DATA_DIR / "backups"
    
    # Banco de dados
    DATABASE_URL: str = Field(
        default="sqlite:///data/cartola.db",
        description="URL de conexão com o banco de dados"
    )
    
    # API Cartola FC
    CARTOLA_API_BASE_URL: str = "https://api.cartolafc.globo.com"
    CARTOLA_API_TIMEOUT: int = 30
    
    # Endpoints da API
    ENDPOINT_MERCADO: str = "/atletas/mercado"
    ENDPOINT_STATUS: str = "/mercado/status"
    ENDPOINT_RODADAS: str = "/rodadas"
    ENDPOINT_PARTIDAS: str = "/partidas"
    ENDPOINT_PONTUADOS: str = "/atletas/pontuados"
    ENDPOINT_CLUBES: str = "/clubes"
    
    # Configurações de escalação
    BUDGET_INICIAL: float = 100.0
    MAX_JOGADORES_MESMO_CLUBE: int = 5
    
    # Esquemas táticos válidos
    ESQUEMAS_VALIDOS: list = [
        "3-4-3", "3-5-2", "4-3-3", "4-4-2", "4-5-1", "5-3-2", "5-4-1"
    ]
    
    # Posições
    POSICOES: dict = {
        1: {"nome": "Goleiro", "abrev": "GOL", "min": 1, "max": 1},
        2: {"nome": "Lateral", "abrev": "LAT", "min": 0, "max": 2},
        3: {"nome": "Zagueiro", "abrev": "ZAG", "min": 2, "max": 3},
        4: {"nome": "Meia", "abrev": "MEI", "min": 3, "max": 5},
        5: {"nome": "Atacante", "abrev": "ATA", "min": 1, "max": 3},
        6: {"nome": "Técnico", "abrev": "TEC", "min": 1, "max": 1}
    }
    
    # Status dos jogadores
    STATUS_JOGADORES: dict = {
        2: "Dúvida",
        3: "Suspenso",
        5: "Contundido",
        6: "Nulo",
        7: "Provável"
    }
    
    # Scouts e pontuações
    SCOUTS: dict = {
        "G": 8.0,      # Gol
        "A": 5.0,      # Assistência
        "SG": 5.0,     # Saldo de Gols
        "FS": 0.5,     # Falta Sofrida
        "FF": 0.8,     # Finalização para Fora
        "FD": 1.2,     # Finalização Defendida
        "FT": 3.0,     # Finalização na Trave
        "DS": 1.5,     # Desarme
        "RB": 1.5,     # Roubada de Bola
        "DD": 3.0,     # Defesa Difícil
        "DP": 7.0,     # Defesa de Pênalti
        "CA": -1.0,    # Cartão Amarelo
        "CV": -3.0,    # Cartão Vermelho
        "GC": -3.0,    # Gol Contra
        "PP": -4.0,    # Pênalti Perdido
        "PC": -1.0,    # Pênalti Cometido
        "FC": -0.3,    # Falta Cometida
        "GS": -1.0,    # Gol Sofrido
        "I": -0.1,     # Impedimento
        "PI": -0.1,    # Passe Incompleto
    }
    
    # Limiares para análise
    PRECO_MAXIMO_VALORIZACAO: float = 10.0
    MEDIA_MINIMA_PONTUACAO: float = 3.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global de configurações
settings = Settings()


# Criar diretórios necessários
settings.DATA_DIR.mkdir(exist_ok=True)
settings.BACKUP_DIR.mkdir(exist_ok=True)
