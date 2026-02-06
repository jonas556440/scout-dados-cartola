"""
Coletor de Scouts - Cartola FC 2026

Coleta e armazena scouts de jogadores após cada rodada.
Mantém histórico completo para análise futura.
"""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

sys.path.append(str(Path(__file__).parent.parent.parent))

from config.settings import settings


class ScoutCollector:
    """
    Coletor de scouts pós-rodada
    
    Responsabilidades:
    - Coletar pontuações após o fim da rodada
    - Atualizar banco de dados com scouts
    - Calcular variações de preço
    - Identificar destaques e decepções
    """
    
    def __init__(self, api_client, db_manager):
        """
        Args:
            api_client: Cliente da API do Cartola
            db_manager: Gerenciador do banco de dados
        """
        self.api = api_client
        self.db = db_manager
        self.ultima_coleta = None
    
    def coletar_scouts_rodada(self, rodada_id: int = None) -> Dict[str, Any]:
        """
        Coleta todos os scouts de uma rodada
        
        Args:
            rodada_id: ID da rodada (None = rodada atual)
            
        Returns:
            Dicionário com resultado da coleta
        """
        resultado = {
            "sucesso": False,
            "rodada_id": rodada_id,
            "total_jogadores": 0,
            "destaques": [],
            "decepcoes": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Obter status do mercado
            status = self.api.get_status_mercado()
            
            if not status:
                resultado["erro"] = "Não foi possível obter status do mercado"
                return resultado
            
            rodada_atual = status.get("rodada_atual", 1)
            if rodada_id is None:
                rodada_id = rodada_atual
            
            resultado["rodada_id"] = rodada_id
            
            # Verificar se rodada já encerrou
            status_mercado = status.get("status_mercado", 0)
            if status_mercado == 1:  # Mercado aberto = rodada não iniciou ainda
                # Coletar rodada anterior
                rodada_id = rodada_id - 1 if rodada_id > 1 else 1
                resultado["rodada_id"] = rodada_id
            
            # Obter pontuações
            pontuados = self.api.get_atletas_pontuados(rodada_id)
            
            if not pontuados:
                resultado["erro"] = f"Sem dados para rodada {rodada_id}"
                return resultado
            
            # Sincronizar com banco de dados
            total = self.db.sync_scouts(pontuados, rodada_id)
            resultado["total_jogadores"] = total
            
            # Identificar destaques
            destaques = self._identificar_destaques(pontuados)
            resultado["destaques"] = destaques
            
            # Identificar decepções
            decepcoes = self._identificar_decepcoes(pontuados)
            resultado["decepcoes"] = decepcoes
            
            # Atualizar status da rodada
            self.db.atualizar_status_rodada(rodada_id, "encerrada")
            
            resultado["sucesso"] = True
            self.ultima_coleta = datetime.now()
            
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def _identificar_destaques(
        self, 
        pontuados: Dict[str, Any], 
        limite: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Identifica os maiores pontuadores da rodada
        
        Returns:
            Lista com os TOP jogadores
        """
        lista = []
        for atleta_id, dados in pontuados.items():
            lista.append({
                "atleta_id": int(atleta_id),
                "apelido": dados.get("apelido", ""),
                "pontuacao": dados.get("pontuacao", 0),
                "posicao": dados.get("posicao_id", 0)
            })
        
        lista.sort(key=lambda x: x["pontuacao"], reverse=True)
        return lista[:limite]
    
    def _identificar_decepcoes(
        self, 
        pontuados: Dict[str, Any], 
        limite: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identifica os piores pontuadores
        
        Returns:
            Lista com os piores jogadores
        """
        lista = []
        for atleta_id, dados in pontuados.items():
            lista.append({
                "atleta_id": int(atleta_id),
                "apelido": dados.get("apelido", ""),
                "pontuacao": dados.get("pontuacao", 0),
                "posicao": dados.get("posicao_id", 0)
            })
        
        # Ordenar do pior para o melhor
        lista.sort(key=lambda x: x["pontuacao"])
        return lista[:limite]
    
    def coletar_mercado_atualizado(self, rodada_id: int = None) -> Dict[str, Any]:
        """
        Coleta dados atualizados do mercado
        
        Atualiza preços e médias de todos os jogadores.
        
        Returns:
            Resultado da coleta
        """
        resultado = {
            "sucesso": False,
            "total_atletas": 0,
            "total_clubes": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Obter dados do mercado
            mercado = self.api.get_mercado()
            
            if not mercado:
                resultado["erro"] = "Não foi possível obter dados do mercado"
                return resultado
            
            atletas = mercado.get("atletas", [])
            clubes = mercado.get("clubes", {})
            
            # Sincronizar clubes
            if clubes:
                total_clubes = self.db.sync_clubes(clubes)
                resultado["total_clubes"] = total_clubes
            
            # Sincronizar atletas
            if atletas:
                total_atletas = self.db.sync_atletas(atletas, rodada_id)
                resultado["total_atletas"] = total_atletas
            
            resultado["sucesso"] = True
            
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def coletar_historico_completo(self, desde_rodada: int = 1) -> Dict[str, Any]:
        """
        Coleta histórico de todas as rodadas finalizadas
        
        Args:
            desde_rodada: Rodada inicial para coleta
            
        Returns:
            Resultado da coleta completa
        """
        resultado = {
            "sucesso": False,
            "rodadas_coletadas": 0,
            "total_scouts": 0,
            "erros": []
        }
        
        try:
            # Obter rodada atual
            status = self.api.get_status_mercado()
            if not status:
                resultado["erros"].append("Não foi possível obter status")
                return resultado
            
            rodada_atual = status.get("rodada_atual", 1)
            
            # Coletar cada rodada
            for rodada in range(desde_rodada, rodada_atual):
                print(f"📥 Coletando rodada {rodada}...")
                
                res = self.coletar_scouts_rodada(rodada)
                
                if res.get("sucesso"):
                    resultado["rodadas_coletadas"] += 1
                    resultado["total_scouts"] += res.get("total_jogadores", 0)
                else:
                    resultado["erros"].append(f"Rodada {rodada}: {res.get('erro')}")
                
                # Pequeno delay para não sobrecarregar API
                time.sleep(0.5)
            
            resultado["sucesso"] = resultado["rodadas_coletadas"] > 0
            
        except Exception as e:
            resultado["erros"].append(str(e))
        
        return resultado
    
    def atualizar_precos(self) -> Dict[str, Any]:
        """
        Atualiza preços de todos os atletas após valorização
        
        Returns:
            Estatísticas de atualização
        """
        resultado = {
            "sucesso": False,
            "valorizaram": 0,
            "desvalorizaram": 0,
            "mantiveram": 0
        }
        
        try:
            mercado = self.api.get_mercado()
            
            if not mercado:
                resultado["erro"] = "Erro ao obter mercado"
                return resultado
            
            atletas = mercado.get("atletas", [])
            
            for atleta in atletas:
                variacao = atleta.get("variacao_num", 0)
                
                if variacao > 0:
                    resultado["valorizaram"] += 1
                elif variacao < 0:
                    resultado["desvalorizaram"] += 1
                else:
                    resultado["mantiveram"] += 1
            
            resultado["sucesso"] = True
            
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def verificar_valorizacao_time(
        self, 
        atletas_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Verifica a valorização/desvalorização do time escalado
        
        Args:
            atletas_ids: Lista de IDs dos atletas escalados
            
        Returns:
            Relatório de valorização
        """
        resultado = {
            "total_variacao": 0.0,
            "detalhes": []
        }
        
        try:
            mercado = self.api.get_mercado()
            
            if not mercado:
                return resultado
            
            atletas = {a.get("atleta_id"): a for a in mercado.get("atletas", [])}
            
            for atleta_id in atletas_ids:
                atleta = atletas.get(atleta_id)
                
                if atleta:
                    variacao = atleta.get("variacao_num", 0)
                    resultado["total_variacao"] += variacao
                    resultado["detalhes"].append({
                        "atleta_id": atleta_id,
                        "apelido": atleta.get("apelido", ""),
                        "variacao": variacao,
                        "preco_atual": atleta.get("preco_num", 0)
                    })
            
            # Ordenar por variação
            resultado["detalhes"].sort(key=lambda x: x["variacao"], reverse=True)
            
        except Exception as e:
            resultado["erro"] = str(e)
        
        return resultado
    
    def agendar_coleta_automatica(self, intervalo_segundos: int = 3600):
        """
        Agenda coleta automática (para uso com scheduler)
        
        Args:
            intervalo_segundos: Intervalo entre coletas
        """
        # Esta função seria usada com schedule ou similar
        pass


# Factory function
def criar_coletor():
    """Cria instância do coletor com dependências"""
    from src.api.cartola_api import CartolaAPI
    from src.database.db_manager import DatabaseManager
    
    api = CartolaAPI()
    db = DatabaseManager()
    
    return ScoutCollector(api, db)


if __name__ == "__main__":
    print("📥 Scout Collector - Cartola FC 2026")
    print("=" * 40)
    
    try:
        coletor = criar_coletor()
        
        # Coletar mercado
        print("\n📊 Coletando dados do mercado...")
        res_mercado = coletor.coletar_mercado_atualizado()
        
        if res_mercado["sucesso"]:
            print(f"   ✅ {res_mercado['total_atletas']} atletas atualizados")
            print(f"   ✅ {res_mercado['total_clubes']} clubes atualizados")
        else:
            print(f"   ❌ Erro: {res_mercado.get('erro')}")
        
        # Coletar scouts da última rodada
        print("\n🎯 Coletando scouts da rodada...")
        res_scouts = coletor.coletar_scouts_rodada()
        
        if res_scouts["sucesso"]:
            print(f"   ✅ {res_scouts['total_jogadores']} scouts registrados")
            print(f"\n   🌟 Destaques:")
            for d in res_scouts["destaques"][:5]:
                print(f"      {d['apelido']}: {d['pontuacao']:.1f} pts")
        else:
            print(f"   ⚠️ {res_scouts.get('erro')}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
