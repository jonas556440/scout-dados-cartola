
import sys
from pathlib import Path
sys.path.append('/root/cartolafc2026')
from src.api.cartola_api import CartolaAPI

api = CartolaAPI()
mercado = api.get_mercado()
atletas = mercado.get('atletas', [])

tecnicos = [a for a in atletas if a.get('posicao_id') == 6]
tecnicos.sort(key=lambda x: x.get('preco_num', 0))

print(f"{'NOME':<20} | {'CLUBE':<10} | {'PREÇO':<6} | {'MÉDIA':<6}")
print("-" * 50)
for tec in tecnicos:
    nome = tec.get('apelido', 'Unknown')
    clube_id = tec.get('clube_id')
    preco = tec.get('preco_num', 0)
    media = tec.get('media_num', 0)
    print(f"{nome:<20} | {clube_id:<10} | {preco:<6.2f} | {media:<6.2f}")
