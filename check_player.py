
import sys
from pathlib import Path
sys.path.append('/root/cartolafc2026')
from src.api.cartola_api import CartolaAPI

api = CartolaAPI()
# Force refresh to ignore cache
mercado = api.get_mercado()
# Check src/api/cartola_api.py to see if get_mercado accepts arguments.
# Based on previous read, CartolaAPI._make_request handles cache. passing use_cache=False if exposed.
# But CartolaAPI.get_mercado() usually calls _make_request.

# Let's check CartolaAPI source code again quickly or just try to use it.
# Re-reading src/api/cartola_api.py showed:
# def get_mercado(self): return self._make_request("/atletas/mercado")

# So I can't pass force_refresh directly unless I modify the code or clear cache manually.
# But for now, let's just inspect what's returned.

atletas = mercado.get('atletas', [])
robert = next((a for a in atletas if 'Robert Renan' in a.get('apelido', '') or 'Robert Renan' in a.get('nome', '')), None)

if robert:
    print(f"Nome: {robert.get('nome')}")
    print(f"Apelido: {robert.get('apelido')}")
    print(f"Status ID: {robert.get('status_id')}")
    print(f"Clube ID: {robert.get('clube_id')}")
    
    # Get club name
    clubes = mercado.get('clubes', {})
    clube = clubes.get(str(robert.get('clube_id')))
    if clube:
        print(f"Clube: {clube.get('nome')} ({clube.get('abreviacao')})")
        
    print(f"Preço: {robert.get('preco_num')}")
else:
    print("Robert Renan não encontrado no mercado.")

# Also check status mapping in settings
from config.settings import settings
print(f"Status Mapping: {settings.STATUS_JOGADORES}")
