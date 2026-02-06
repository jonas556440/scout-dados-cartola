
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from src.analysis.score_predictor import ScorePredictor

def run_analysis():
    predictor = ScorePredictor()
    
    jogos = [
        {
            "mandante": "Flamengo", "visitante": "Corinthians",
            "params": {"forca_mandante": 88, "forca_visitante": 72, "posicao_mandante": 1, "posicao_visitante": 5, "forma_mandante": "VVVVV", "forma_visitante": "VEDVV"}
        },
        {
            "mandante": "Mirassol", "visitante": "Novorizontino",
            "params": {"forca_mandante": 68, "forca_visitante": 62, "posicao_mandante": 3, "posicao_visitante": 4, "forma_mandante": "VVEEV", "forma_visitante": "VEEDD"}
        },
        {
            "mandante": "Botafogo", "visitante": "Fluminense",
            "params": {"forca_mandante": 82, "forca_visitante": 78, "posicao_mandante": 2, "posicao_visitante": 3, "forma_mandante": "VVVEV", "forma_visitante": "VVEDV"}
        },
        {
            "mandante": "Botafogo SP", "visitante": "Palmeiras",
            "params": {"forca_mandante": 40, "forca_visitante": 92, "posicao_mandante": 12, "posicao_visitante": 1, "forma_mandante": "DDEDD", "forma_visitante": "VVVVV"}
        },
        {
            "mandante": "Madureira", "visitante": "Vasco da Gama",
            "params": {"forca_mandante": 35, "forca_visitante": 80, "posicao_mandante": 9, "posicao_visitante": 3, "forma_mandante": "DEDED", "forma_visitante": "VVVEV"}
        }
    ]

    print(f"{'JOGO':<40} | {'PREVISÃO':<8} | {'TOP 3 PLACARES (PROBABILIDADE)':<45} | {'CONFIA.':<8}")
    print("-" * 115)

    for jogo in jogos:
        previsao = predictor.prever_confronto(
            mandante=jogo["mandante"],
            visitante=jogo["visitante"],
            **jogo["params"]
        )
        
        # Format top 3 scores
        top_3 = ", ".join([f"{p} ({prob:.0f}%)" for p, prob in previsao.top_placares[:3]])
        
        # Determine confidence label
        conf = previsao.confianca
        
        print(f"{jogo['mandante']} vs {jogo['visitante']:<20} | {previsao.placar_provavel:<8} | {top_3:<45} | {conf}%")

if __name__ == "__main__":
    run_analysis()
