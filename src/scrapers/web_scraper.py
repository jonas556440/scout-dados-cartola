"""
Web Scraper - Busca de Notícias e Escalações
Cartola FC 2026

Busca informações de fontes externas:
1. GE.globo.com - Notícias oficiais dos times
2. Cartola PFC - Análises especializadas
3. Twitter/X - Notícias de última hora
4. Sites oficiais dos clubes

Informações coletadas:
- Escalações prováveis
- Jogadores suspensos (cartões)
- Jogadores lesionados
- Times que vão poupar/jogar reservas
- Desfalques de última hora
"""
import sys
import re
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json

sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False
    print("⚠️  requests e BeautifulSoup não instalados. Execute: pip install requests beautifulsoup4 lxml")

logger = logging.getLogger(__name__)


@dataclass
class NoticiaTime:
    """Notícia sobre um time"""
    clube_abrev: str
    titulo: str
    resumo: str
    link: str
    fonte: str
    data: datetime
    tipo: str  # "desfalque", "escalacao", "reservas", "geral"
    
    # Informações extraídas
    jogadores_mencionados: List[str] = field(default_factory=list)
    lesionados: List[str] = field(default_factory=list)
    suspensos: List[str] = field(default_factory=list)
    duvidas: List[str] = field(default_factory=list)
    vai_poupar: bool = False


class WebScraper:
    """
    Scraper de notícias sobre times do Cartola FC
    
    Busca em múltiplas fontes para identificar:
    - Jogadores que não vão jogar
    - Times que vão jogar com reservas
    - Escalações prováveis
    """
    
    # Mapeamento de nomes dos times (varia por fonte)
    MAPEAMENTO_TIMES = {
        "flamengo": "FLA",
        "palmeiras": "PAL",
        "botafogo": "BOT",
        "internacional": "INT",
        "corinthians": "COR",
        "sao-paulo": "SAO",
        "fluminense": "FLU",
        "atletico-mg": "CAM",
        "gremio": "GRE",
        "cruzeiro": "CRU",
        "santos": "SAN",
        "vasco": "VAS",
        "bahia": "BAH",
        "athletico-pr": "CAP",
        "fortaleza": "FOR",
        "bragantino": "RBB",
        "cuiaba": "CUI",
        "vitoria": "VIT",
        "juventude": "JUV",
        "criciuma": "CRI",
        "remo": "REM",
        "mirassol": "MIR",
        "chapecoense": "CHA",
        "coritiba": "CFC",
    }
    
    # Palavras-chave para identificar desfalques
    KEYWORDS_LESAO = [
        "lesionado", "lesão", "machucado", "contundido", "departamento médico",
        "cirurgia", "tratamento", "se recupera", "dor", "problema físico"
    ]
    
    KEYWORDS_SUSPENSAO = [
        "suspenso", "cartão", "amarelo", "vermelho", "expulso", "punido",
        "gancho", "cumpre suspensão", "não pode jogar"
    ]
    
    KEYWORDS_DUVIDA = [
        "dúvida", "avaliado", "reavaliado", "em transição", "pode jogar",
        "aguarda exames", "indefinido", "decisão de última hora"
    ]
    
    KEYWORDS_POUPAR = [
        "poupar", "preservar", "descansar", "rodar elenco", "time misto",
        "reservas", "banco", "não deve começar jogando", "alternativo"
    ]
    
    def __init__(self, cache_duration_minutes: int = 30):
        self.cache_duration = timedelta(minutes=cache_duration_minutes)
        self.cache: Dict[str, Tuple[datetime, List[NoticiaTime]]] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def buscar_noticias_time(self, clube_abrev: str) -> List[NoticiaTime]:
        """
        Busca notícias sobre um time específico
        
        Args:
            clube_abrev: Abreviação do time (FLA, PAL, etc)
            
        Returns:
            Lista de notícias encontradas
        """
        # Verificar cache
        if clube_abrev in self.cache:
            timestamp, noticias = self.cache[clube_abrev]
            if datetime.now() - timestamp < self.cache_duration:
                logger.info(f"✅ Cache válido para {clube_abrev}")
                return noticias
        
        noticias = []
        
        # Buscar em múltiplas fontes
        noticias.extend(self._buscar_ge_globo(clube_abrev))
        noticias.extend(self._buscar_cartola_pfc(clube_abrev))
        
        # Salvar no cache
        self.cache[clube_abrev] = (datetime.now(), noticias)
        
        logger.info(f"📰 Encontradas {len(noticias)} notícias para {clube_abrev}")
        return noticias
    
    def _buscar_ge_globo(self, clube_abrev: str) -> List[NoticiaTime]:
        """Busca notícias no GE.globo.com"""
        noticias = []
        
        if not HAS_SCRAPING:
            return noticias
        
        # Encontrar slug do time
        slug = None
        for s, abrev in self.MAPEAMENTO_TIMES.items():
            if abrev == clube_abrev:
                slug = s
                break
        
        if not slug:
            return noticias
        
        try:
            # URL de notícias do time
            urls = [
                f"https://ge.globo.com/futebol/times/{slug}/",
                f"https://ge.globo.com/{slug}/",
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.text, 'lxml')
                    
                    # Buscar notícias recentes
                    articles = soup.find_all(['article', 'div'], class_=re.compile(r'feed-post|bastian-feed-item|post'))[:10]
                    
                    for article in articles:
                        try:
                            # Extrair título
                            titulo_elem = article.find(['h2', 'h3', 'a'], class_=re.compile(r'feed-post-link|title'))
                            if not titulo_elem:
                                continue
                            
                            titulo = titulo_elem.get_text(strip=True)
                            link_elem = titulo_elem if titulo_elem.name == 'a' else titulo_elem.find('a')
                            link = link_elem.get('href', '') if link_elem else ''
                            
                            # Extrair resumo
                            resumo_elem = article.find(['p', 'div'], class_=re.compile(r'summary|resumo|description'))
                            resumo = resumo_elem.get_text(strip=True) if resumo_elem else ''
                            
                            # Identificar tipo de notícia
                            texto_completo = (titulo + ' ' + resumo).lower()
                            tipo = self._identificar_tipo_noticia(texto_completo)
                            
                            # Extrair informações
                            lesionados = self._extrair_jogadores(texto_completo, self.KEYWORDS_LESAO)
                            suspensos = self._extrair_jogadores(texto_completo, self.KEYWORDS_SUSPENSAO)
                            duvidas = self._extrair_jogadores(texto_completo, self.KEYWORDS_DUVIDA)
                            vai_poupar = any(kw in texto_completo for kw in self.KEYWORDS_POUPAR)
                            
                            noticia = NoticiaTime(
                                clube_abrev=clube_abrev,
                                titulo=titulo,
                                resumo=resumo[:200],
                                link=link,
                                fonte="GE.globo.com",
                                data=datetime.now(),
                                tipo=tipo,
                                lesionados=lesionados,
                                suspensos=suspensos,
                                duvidas=duvidas,
                                vai_poupar=vai_poupar,
                            )
                            
                            noticias.append(noticia)
                            
                        except Exception as e:
                            logger.debug(f"Erro ao processar artigo: {e}")
                            continue
                    
                    # Se encontrou notícias, não precisa tentar outras URLs
                    if noticias:
                        break
                        
                except requests.RequestException as e:
                    logger.debug(f"Erro ao acessar {url}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Erro ao buscar GE.globo.com para {clube_abrev}: {e}")
        
        return noticias
    
    def _buscar_cartola_pfc(self, clube_abrev: str) -> List[NoticiaTime]:
        """Busca análises no Cartola PFC (não implementado)"""
        return []
    
    def _identificar_tipo_noticia(self, texto: str) -> str:
        """Identifica o tipo de notícia pelo conteúdo"""
        texto_lower = texto.lower()
        
        if any(kw in texto_lower for kw in self.KEYWORDS_LESAO):
            return "desfalque"
        elif any(kw in texto_lower for kw in self.KEYWORDS_SUSPENSAO):
            return "desfalque"
        elif any(kw in texto_lower for kw in self.KEYWORDS_DUVIDA):
            return "escalacao"
        elif any(kw in texto_lower for kw in self.KEYWORDS_POUPAR):
            return "reservas"
        elif "escalação" in texto_lower or "time" in texto_lower:
            return "escalacao"
        else:
            return "geral"
    
    def _extrair_jogadores(self, texto: str, keywords: List[str]) -> List[str]:
        """
        Extrai nomes de jogadores mencionados próximos às keywords
        
        Procura por padrões como:
        - "[Nome] está lesionado"
        - "Com lesão, [Nome] é desfalque"
        """
        jogadores = []
        texto_lower = texto.lower()
        
        for keyword in keywords:
            if keyword not in texto_lower:
                continue
            
            # Procurar nomes próprios próximos à keyword
            # Pattern: palavra começando com maiúscula (possível nome de jogador)
            pattern = r'\b[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+(?:\s+[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+)*\b'
            
            # Buscar em uma janela de 50 caracteres ao redor da keyword
            idx = texto.find(keyword)
            if idx == -1:
                idx = texto_lower.find(keyword)
            
            if idx != -1:
                inicio = max(0, idx - 50)
                fim = min(len(texto), idx + len(keyword) + 50)
                trecho = texto[inicio:fim]
                
                nomes = re.findall(pattern, trecho)
                # Filtrar palavras comuns que não são nomes
                palavras_ignorar = {'O', 'A', 'E', 'De', 'Da', 'Do', 'Com', 'Sem', 'Pelo', 'Para'}
                nomes = [n for n in nomes if n not in palavras_ignorar and len(n) > 2]
                jogadores.extend(nomes[:2])  # Máximo 2 nomes por keyword
        
        return list(set(jogadores))[:5]  # Máximo 5 jogadores
    
    def buscar_noticias_rodada(self, clubes: List[str]) -> Dict[str, List[NoticiaTime]]:
        """
        Busca notícias de todos os times da rodada
        
        Args:
            clubes: Lista de abreviações dos times
            
        Returns:
            Dict com noticias por time
        """
        resultado = {}
        
        for i, clube in enumerate(clubes):
            logger.info(f"🔍 Buscando notícias {clube} ({i+1}/{len(clubes)})")
            resultado[clube] = self.buscar_noticias_time(clube)
            
            # Rate limiting: esperar entre requisições
            if i < len(clubes) - 1:
                time.sleep(1)
        
        return resultado
    
    def gerar_resumo_desfalques(self, noticias: List[NoticiaTime]) -> Dict[str, Any]:
        """
        Gera resumo dos desfalques de um time
        
        Returns:
            Dict com lista de lesionados, suspensos, etc
        """
        lesionados = set()
        suspensos = set()
        duvidas = set()
        vai_poupar = False
        noticias_relevantes = []
        
        for noticia in noticias:
            lesionados.update(noticia.lesionados)
            suspensos.update(noticia.suspensos)
            duvidas.update(noticia.duvidas)
            vai_poupar = vai_poupar or noticia.vai_poupar
            
            if noticia.tipo in ['desfalque', 'escalacao', 'reservas']:
                noticias_relevantes.append({
                    'titulo': noticia.titulo,
                    'link': noticia.link,
                    'tipo': noticia.tipo,
                })
        
        return {
            'lesionados': list(lesionados),
            'suspensos': list(suspensos),
            'duvidas': list(duvidas),
            'vai_poupar': vai_poupar,
            'noticias': noticias_relevantes[:3],  # Top 3 mais relevantes
            'total_noticias': len(noticias),
        }


# Função auxiliar para integração com match_analyzer
def aplicar_penalizacoes_noticias(
    scraper: WebScraper,
    clubes: List[str],
    forca_times: Dict[str, float]
) -> Dict[str, float]:
    """
    Aplica penalizações baseadas em notícias
    
    Args:
        scraper: Instância do WebScraper
        clubes: Lista de abreviações dos times
        forca_times: Dict com força atual de cada time
        
    Returns:
        Dict com força ajustada
    """
    forca_ajustada = forca_times.copy()
    
    noticias_rodada = scraper.buscar_noticias_rodada(clubes)
    
    for clube, noticias in noticias_rodada.items():
        resumo = scraper.gerar_resumo_desfalques(noticias)
        
        penalizacao = 0.0
        
        # Cada jogador lesionado = -3 pontos
        penalizacao += len(resumo['lesionados']) * 3
        
        # Cada suspenso = -4 pontos
        penalizacao += len(resumo['suspensos']) * 4
        
        # Cada dúvida = -1.5 pontos
        penalizacao += len(resumo['duvidas']) * 1.5
        
        # Vai poupar = -10 pontos (time reserva)
        if resumo['vai_poupar']:
            penalizacao += 10
        
        if penalizacao > 0:
            logger.info(f"⚠️  {clube}: -{penalizacao:.1f} pontos (lesionados: {len(resumo['lesionados'])}, suspensos: {len(resumo['suspensos'])})")
        
        # Aplicar penalização
        if clube in forca_ajustada:
            forca_ajustada[clube] = max(20, forca_ajustada[clube] - penalizacao)
    
    return forca_ajustada


if __name__ == "__main__":
    # Teste do scraper
    logging.basicConfig(level=logging.INFO)
    
    scraper = WebScraper()
    
    print("🧪 Testando busca de notícias...")
    print("=" * 60)
    
    # Testar com Flamengo
    noticias = scraper.buscar_noticias_time("FLA")
    
    if noticias:
        print(f"\n✅ Encontradas {len(noticias)} notícias do Flamengo:")
        for i, noticia in enumerate(noticias[:3], 1):
            print(f"\n{i}. {noticia.titulo}")
            print(f"   Tipo: {noticia.tipo}")
            print(f"   Link: {noticia.link}")
            if noticia.lesionados:
                print(f"   Lesionados: {', '.join(noticia.lesionados)}")
            if noticia.suspensos:
                print(f"   Suspensos: {', '.join(noticia.suspensos)}")
        
        resumo = scraper.gerar_resumo_desfalques(noticias)
        print(f"\n📋 RESUMO:")
        print(f"   Lesionados: {resumo['lesionados']}")
        print(f"   Suspensos: {resumo['suspensos']}")
        print(f"   Dúvidas: {resumo['duvidas']}")
        print(f"   Vai poupar: {resumo['vai_poupar']}")
    else:
        print("❌ Nenhuma notícia encontrada")
