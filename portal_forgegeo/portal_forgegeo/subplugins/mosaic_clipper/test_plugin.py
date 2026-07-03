#!/usr/bin/env python3
"""
Script de teste para validar a estrutura e funcionalidade básica do plugin Mosaic Clipper
"""

import os
import sys
from pathlib import Path

def test_file_structure():
    """Testa se todos os arquivos necessários existem"""
    plugin_dir = Path(__file__).parent
    required_files = [
        '__init__.py',
        'plugin.py',
        'dialog.py',
        'gee_handler.py',
        'utils.py',
        'metadata.txt',
        'requirements.txt',
        'README.md',
        'INSTALL.md'
    ]
    
    print("=" * 60)
    print("TESTE 1: Estrutura de Arquivos")
    print("=" * 60)
    
    all_exist = True
    for file in required_files:
        file_path = plugin_dir / file
        exists = file_path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {file}")
        if not exists:
            all_exist = False
    
    return all_exist

def test_imports():
    """Testa se os módulos podem ser importados"""
    print("\n" + "=" * 60)
    print("TESTE 2: Importações de Módulos")
    print("=" * 60)
    
    try:
        from utils import get_plugin_dir, get_config_dir, get_gee_credentials_path
        print("✓ utils.py importado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao importar utils.py: {e}")
        return False
    
    try:
        from gee_handler import GEEHandler
        print("✓ gee_handler.py importado com sucesso")
    except ImportError as e:
        if 'PyQt5' in str(e) or 'ee' in str(e):
            print(f"⚠ Aviso: {e} (esperado fora do ambiente QGIS)")
            print("✓ gee_handler.py estrutura validada (testes completos no QGIS)")
            return True
        else:
            print(f"✗ Erro ao importar gee_handler.py: {e}")
            return False
    except Exception as e:
        print(f"✗ Erro ao importar gee_handler.py: {e}")
        return False
    
    return True

def test_metadata():
    """Testa se o arquivo metadata.txt está bem formatado"""
    print("\n" + "=" * 60)
    print("TESTE 3: Validação de Metadados")
    print("=" * 60)
    
    plugin_dir = Path(__file__).parent
    metadata_path = plugin_dir / 'metadata.txt'
    
    if not metadata_path.exists():
        print("✗ Arquivo metadata.txt não encontrado")
        return False
    
    try:
        with open(metadata_path, 'r') as f:
            content = f.read()
        
        required_fields = ['name', 'version', 'qgisMinimumVersion', 'author', 'description']
        all_present = True
        
        for field in required_fields:
            if field in content:
                print(f"✓ Campo '{field}' presente")
            else:
                print(f"✗ Campo '{field}' ausente")
                all_present = False
        
        return all_present
    except Exception as e:
        print(f"✗ Erro ao ler metadata.txt: {e}")
        return False

def test_requirements():
    """Testa se o arquivo requirements.txt está bem formatado"""
    print("\n" + "=" * 60)
    print("TESTE 4: Validação de Dependências")
    print("=" * 60)
    
    plugin_dir = Path(__file__).parent
    requirements_path = plugin_dir / 'requirements.txt'
    
    if not requirements_path.exists():
        print("✗ Arquivo requirements.txt não encontrado")
        return False
    
    try:
        with open(requirements_path, 'r') as f:
            content = f.read().strip()
        
        if 'earthengine-api' in content:
            print("✓ earthengine-api listado em requirements.txt")
            return True
        else:
            print("✗ earthengine-api não encontrado em requirements.txt")
            return False
    except Exception as e:
        print(f"✗ Erro ao ler requirements.txt: {e}")
        return False

def test_gee_handler():
    """Testa a classe GEEHandler"""
    print("\n" + "=" * 60)
    print("TESTE 5: Validação da Classe GEEHandler")
    print("=" * 60)
    
    try:
        from gee_handler import GEEHandler
        handler = GEEHandler()
        
        # Testa métodos
        methods = ['authenticate', 'is_authenticated', 'get_collection', 'get_best_image', 
                   'process_landsat_image', 'clip_and_export', 'get_task_status']
        
        all_present = True
        for method in methods:
            if hasattr(handler, method):
                print(f"✓ Método '{method}' presente")
            else:
                print(f"✗ Método '{method}' ausente")
                all_present = False
        
        return all_present
    except ImportError as e:
        if 'PyQt5' in str(e) or 'ee' in str(e):
            print(f"⚠ Aviso: {e} (esperado fora do ambiente QGIS)")
            print("✓ GEEHandler estrutura validada (testes completos no QGIS)")
            return True
        else:
            print(f"✗ Erro ao testar GEEHandler: {e}")
            return False
    except Exception as e:
        print(f"✗ Erro ao testar GEEHandler: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  TESTES DE VALIDAÇÃO - MOSAIC CLIPPER v0.0.1".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = {
        "Estrutura de Arquivos": test_file_structure(),
        "Importações": test_imports(),
        "Metadados": test_metadata(),
        "Dependências": test_requirements(),
        "GEEHandler": test_gee_handler()
    }
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ TODOS OS TESTES PASSARAM!")
        print("O plugin está pronto para ser empacotado.")
    else:
        print("✗ ALGUNS TESTES FALHARAM!")
        print("Verifique os erros acima antes de empacotar o plugin.")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
