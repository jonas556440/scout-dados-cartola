#!/usr/bin/env python3
"""
Script de setup e instalação do Cartola FC 2026
"""
import subprocess
import sys
import os
from pathlib import Path


def instalar_dependencias():
    """Instala dependências do requirements.txt"""
    print("📦 Instalando dependências...")
    
    req_file = Path(__file__).parent / "requirements.txt"
    
    if not req_file.exists():
        print("❌ Arquivo requirements.txt não encontrado!")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(req_file)
        ])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False


def criar_estrutura_dados():
    """Cria diretórios para dados"""
    print("\n📁 Criando estrutura de dados...")
    
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    print(f"✅ Diretório criado: {data_dir}")


def inicializar_banco():
    """Inicializa o banco de dados"""
    print("\n🗄️ Inicializando banco de dados...")
    
    try:
        # Adicionar path do projeto
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        stats = db.get_estatisticas_gerais()
        
        print(f"✅ Banco inicializado!")
        print(f"   - Posições: 6")
        print(f"   - Atletas: {stats['total_atletas']}")
        print(f"   - Clubes: {stats['total_clubes']}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        return False


def testar_api():
    """Testa conexão com a API"""
    print("\n🌐 Testando conexão com API...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.api.cartola_api import CartolaAPI
        
        api = CartolaAPI()
        status = api.get_status_mercado()
        
        if status:
            rodada = status.get("rodada_atual", "?")
            print(f"✅ API funcionando! Rodada atual: {rodada}")
            return True
        else:
            print("⚠️ API retornou vazio (pode estar fora do ar)")
            return True  # Não é erro crítico
            
    except Exception as e:
        print(f"⚠️ Erro ao testar API: {e}")
        return True  # Não é erro crítico


def sincronizar_dados():
    """Sincroniza dados iniciais"""
    print("\n📥 Sincronizando dados iniciais...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.scrapers.scout_collector import criar_coletor
        
        coletor = criar_coletor()
        resultado = coletor.coletar_mercado_atualizado()
        
        if resultado["sucesso"]:
            print(f"✅ Dados sincronizados!")
            print(f"   - Atletas: {resultado['total_atletas']}")
            print(f"   - Clubes: {resultado['total_clubes']}")
            return True
        else:
            print(f"⚠️ Sincronização incompleta: {resultado.get('erro')}")
            return True
            
    except Exception as e:
        print(f"⚠️ Erro na sincronização: {e}")
        return True


def main():
    """Executa setup completo"""
    print("=" * 50)
    print("⚽ CARTOLA FC 2026 - Setup")
    print("=" * 50)
    
    etapas = [
        ("Dependências", instalar_dependencias),
        ("Estrutura", criar_estrutura_dados),
        ("Banco de Dados", inicializar_banco),
        ("API", testar_api),
        ("Sincronização", sincronizar_dados),
    ]
    
    sucesso = True
    for nome, func in etapas:
        print(f"\n{'='*50}")
        print(f"Etapa: {nome}")
        print("="*50)
        
        if not func():
            sucesso = False
            print(f"\n❌ Falha na etapa: {nome}")
            if nome == "Dependências":
                break  # Dependências são críticas
    
    print("\n" + "=" * 50)
    
    if sucesso:
        print("✅ Setup concluído com sucesso!")
        print("\n📌 Para iniciar:")
        print("   python main.py")
        print("\n📌 Ou use comandos diretos:")
        print("   python main.py status")
        print("   python main.py escalar")
        print("   python main.py mercado")
    else:
        print("⚠️ Setup concluído com avisos.")
        print("Verifique os erros acima.")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
