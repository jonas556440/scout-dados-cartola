#!/usr/bin/env python3
"""
Script de healthcheck para monitoramento externo
Retorna exit code 0 se OK, 1 se falha

Uso:
    python healthcheck.py
    
Pode ser usado com cron, systemd, ou ferramentas de monitoramento
"""
import sys
import requests
from datetime import datetime

API_URL = "http://localhost:8000"
TIMEOUT = 5

def check_health():
    """Verifica se a API está saudável"""
    try:
        # 1. Verificar endpoint root
        response = requests.get(f"{API_URL}/", timeout=TIMEOUT)
        if response.status_code != 200:
            print(f"❌ [{datetime.now()}] Endpoint root retornou {response.status_code}")
            return False
        
        # 2. Verificar se status do mercado responde
        response = requests.get(f"{API_URL}/api/status", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ [{datetime.now()}] API OK - Rodada {data.get('rodadaAtual', '?')}")
            return True
        elif response.status_code == 503:
            # 503 é esperado se a API do Cartola estiver fora
            print(f"⚠️  [{datetime.now()}] API OK mas Cartola indisponível (503)")
            return True  # Servidor está funcionando
        else:
            print(f"❌ [{datetime.now()}] Status retornou {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ [{datetime.now()}] TIMEOUT após {TIMEOUT}s")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ [{datetime.now()}] Erro de conexão - servidor pode estar FORA")
        return False
    except Exception as e:
        print(f"❌ [{datetime.now()}] Erro: {e}")
        return False

if __name__ == "__main__":
    is_healthy = check_health()
    sys.exit(0 if is_healthy else 1)
