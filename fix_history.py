import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from src.database.history_manager import HistoryManager
from src.database.models import PatrimonioEvolucao

def fix_history():
    hm = HistoryManager()
    session = hm.get_session()

    print("Corrigindo historico para Rodada 1...")
    
    # Inserir/Atualizar para Time Valorização
    patrimonio_val = session.query(PatrimonioEvolucao).filter_by(
        rodada_id=1, 
        tipo='valorizacao'
    ).first()

    if not patrimonio_val:
        patrimonio_val = PatrimonioEvolucao(
            rodada_id=1,
            tipo='valorizacao',
            cartoletas_inicio=100.0,
            cartoletas_fim=108.0,
            custo_time=85.0, # Estimado
            cartoletas_em_caixa=15.0,
            valorizacao_obtida=8.0,
            pontuacao_rodada=50.0, # Estimado
            pontuacao_acumulada=50.0
        )
        session.add(patrimonio_val)
        print("Criado registro de valorização (108 C$)")
    else:
        patrimonio_val.cartoletas_fim = 108.0
        patrimonio_val.valorizacao_obtida = 8.0
        print("Atualizado registro de valorização (108 C$)")

    # Inserir/Atualizar para Time Pontuação (assumindo que segue o mesmo cofre ou similar)
    patrimonio_pts = session.query(PatrimonioEvolucao).filter_by(
        rodada_id=1, 
        tipo='pontuacao'
    ).first()

    if not patrimonio_pts:
        patrimonio_pts = PatrimonioEvolucao(
            rodada_id=1,
            tipo='pontuacao',
            cartoletas_inicio=100.0,
            cartoletas_fim=108.0, # Aplicando o lucro ao orçamento de pontuação também
            custo_time=95.0,
            cartoletas_em_caixa=5.0,
            valorizacao_obtida=8.0,
            pontuacao_rodada=60.0,
            pontuacao_acumulada=60.0
        )
        session.add(patrimonio_pts)
        print("Criado registro de pontuação (108 C$)")
    else:
        patrimonio_pts.cartoletas_fim = 108.0
        print("Atualizado registro de pontuação (108 C$)")

    session.commit()
    session.close()
    print("Concluido.")

if __name__ == "__main__":
    fix_history()
