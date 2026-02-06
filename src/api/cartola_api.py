"""
Cliente da API oficial do Cartola FC
"""
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
import time
import sys
import logging
sys.path.append('/root/cartolafc2026')

from config.settings import settings

logger = logging.getLogger(__name__)


class CartolaAPIError(Exception):
    """Exceção para erros da API do Cartola"""
    pass


class CartolaAPI:
    """
    Cliente para a API oficial do Cartola FC (Globo)
    
    Endpoints principais:
    - /atletas/mercado - Todos os jogadores disponíveis
    - /mercado/status - Status do mercado
    - /atletas/pontuados - Scouts após a rodada
    - /partidas/{rodada} - Jogos da rodada
    - /rodadas - Informações das rodadas
    """
    
    def __init__(self):
        self.base_url = settings.CARTOLA_API_BASE_URL
        self.timeout = 15  # Reduzido de 30s para 15s
        self.max_retries = 3
        self.retry_delay = 1  # segundos entre tentativas
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
        })
        self._cache = {}
        self._cache_timeout = 300  # 5 minutos
    
    def _make_request(self, endpoint: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Faz requisição à API com cache opcional e retry automático
        """
        url = f"{self.base_url}{endpoint}"
        cache_key = endpoint
        
        # Verificar cache
        if use_cache and cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if time.time() - cached_time < self._cache_timeout:
                logger.debug(f"Cache hit: {endpoint}")
                return cached_data
        
        # Retry loop
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Requisição {endpoint} (tentativa {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                # Atualizar cache
                self._cache[cache_key] = (data, time.time())
                logger.info(f"✅ {endpoint} OK")
                
                return data
                
            except requests.exceptions.Timeout as e:
                last_error = f"Timeout ao acessar {url}"
                logger.warning(f"⏱️ Timeout (tentativa {attempt + 1}): {endpoint}")
            except requests.exceptions.HTTPError as e:
                last_error = f"Erro HTTP {e.response.status_code}: {url}"
                logger.error(f"❌ HTTP Error {e.response.status_code}: {endpoint}")
                # Não fazer retry em erros 4xx (client errors)
                if 400 <= e.response.status_code < 500:
                    break
            except requests.exceptions.RequestException as e:
                last_error = f"Erro de conexão: {e}"
                logger.warning(f"🔌 Conexão falhou (tentativa {attempt + 1}): {endpoint}")
            except ValueError as e:
                last_error = f"Erro ao decodificar JSON: {e}"
                logger.error(f"📄 JSON inválido: {endpoint}")
                break
            
            # Aguardar antes de retry (exceto na última tentativa)
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
        
        # Todas as tentativas falharam
        logger.error(f"❌ FALHA TOTAL após {self.max_retries} tentativas: {endpoint}")
        logger.error(f"Último erro: {last_error}")
        return None  # Retornar None ao invés de raise para não derrubar o servidor
    
    def get_mercado(self) -> Optional[Dict[str, Any]]:
        """
        Obtém todos os atletas disponíveis no mercado
        
        Returns:
            Dict contendo:
            - atletas: Lista de jogadores
            - clubes: Dicionário de clubes
            - posicoes: Dicionário de posições
            - status: Dicionário de status
            - rodada_atual: Número da rodada atual
            
            None se a API falhar após todas as tentativas
        """
        result = self._make_request(settings.ENDPOINT_MERCADO)
        if result is None:
            logger.error("get_mercado retornou None - API indisponível")
        return result
    
    def get_atletas(self) -> List[Dict[str, Any]]:
        """
        Obtém lista de todos os atletas
        """
        mercado = self.get_mercado()
        return mercado.get("atletas", [])
    
    def get_clubes(self) -> Dict[str, Any]:
        """
        Obtém dicionário de clubes
        """
        mercado = self.get_mercado()
        return mercado.get("clubes", {})
    
    def get_status_mercado(self) -> Dict[str, Any]:
        """
        Obtém status do mercado (aberto/fechado)
        
        Returns:
            Dict com:
            - status_mercado: 1 (aberto) ou 2 (fechado)
            - rodada_atual: Número da rodada
            - tempo_restante: Tempo até fechar (se aberto)
        """
        return self._make_request(settings.ENDPOINT_STATUS, use_cache=False)
    
    def get_atletas_pontuados(self) -> Dict[str, Any]:
        """
        Obtém pontuação e scouts dos atletas após a rodada
        
        Returns:
            Dict onde a chave é o atleta_id e valor contém:
            - pontuacao: Pontuação total
            - scout: Dict com os scouts individuais
        """
        return self._make_request(settings.ENDPOINT_PONTUADOS, use_cache=False)
    
    def get_partidas(self, rodada: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém partidas de uma rodada específica
        
        Args:
            rodada: Número da rodada (None = rodada atual)
        """
        endpoint = settings.ENDPOINT_PARTIDAS
        if rodada:
            endpoint = f"{endpoint}/{rodada}"
        return self._make_request(endpoint)
    
    def get_rodadas(self) -> List[Dict[str, Any]]:
        """
        Obtém informações de todas as rodadas
        """
        return self._make_request(settings.ENDPOINT_RODADAS)
    
    def get_atleta_por_id(self, atleta_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um atleta específico por ID
        """
        atletas = self.get_atletas()
        for atleta in atletas:
            if atleta.get("atleta_id") == atleta_id:
                return atleta
        return None
    
    def get_atletas_por_clube(self, clube_id: int) -> List[Dict[str, Any]]:
        """
        Busca todos os atletas de um clube
        """
        atletas = self.get_atletas()
        return [a for a in atletas if a.get("clube_id") == clube_id]
    
    def get_atletas_por_posicao(self, posicao_id: int) -> List[Dict[str, Any]]:
        """
        Busca todos os atletas de uma posição
        """
        atletas = self.get_atletas()
        return [a for a in atletas if a.get("posicao_id") == posicao_id]
    
    def get_atletas_provaveis(self) -> List[Dict[str, Any]]:
        """
        Busca apenas atletas com status "Provável" (status_id = 7)
        """
        atletas = self.get_atletas()
        return [a for a in atletas if a.get("status_id") == 7]
    
    def get_atletas_baratos(self, preco_maximo: float = 10.0) -> List[Dict[str, Any]]:
        """
        Busca atletas prováveis abaixo de um preço máximo
        """
        atletas = self.get_atletas_provaveis()
        return [a for a in atletas if a.get("preco_num", 100) <= preco_maximo]
    
    def limpar_cache(self):
        """Limpa o cache de requisições"""
        self._cache.clear()


# Instância global da API
cartola_api = CartolaAPI()


if __name__ == "__main__":
    # Teste da API
    api = CartolaAPI()
    
    print("🔄 Testando conexão com API do Cartola FC...")
    
    try:
        mercado = api.get_mercado()
        atletas = mercado.get("atletas", [])
        clubes = mercado.get("clubes", {})
        
        print(f"✅ Conexão OK!")
        print(f"📊 Total de atletas: {len(atletas)}")
        print(f"🏟️ Total de clubes: {len(clubes)}")
        
        # Mostrar alguns atletas prováveis baratos
        baratos = api.get_atletas_baratos(preco_maximo=6.0)
        print(f"\n💰 Atletas prováveis até C$6.00: {len(baratos)}")
        
        for atleta in baratos[:5]:
            print(f"  - {atleta['apelido']} ({atleta['posicao_id']}) - C${atleta['preco_num']}")
            
    except CartolaAPIError as e:
        print(f"❌ Erro: {e}")
