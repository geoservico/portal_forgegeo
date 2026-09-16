import os
from pathlib import Path

def get_plugin_dir():
    """Retorna o diretório do plugin"""
    return Path(__file__).parent

def get_config_dir():
    """Retorna o diretório de configuração do usuário"""
    return Path.home() / '.config' / 'mosaic_clipper'

def ensure_config_dir():
    """Cria o diretório de configuração se não existir"""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_gee_credentials_path():
    """Retorna o caminho para as credenciais do GEE"""
    return Path.home() / '.config' / 'earthengine' / 'credentials'

def gee_is_authenticated():
    """Verifica se GEE está autenticado"""
    return get_gee_credentials_path().exists()

def format_file_name(layer_name, year, image_id):
    """Formata o nome do arquivo para exportação"""
    # Remove caracteres inválidos
    safe_layer_name = "".join(c for c in layer_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    safe_image_id = "".join(c for c in image_id if c.isalnum() or c in ('_', '-')).rstrip()
    
    return f"{safe_layer_name}_{year}_{safe_image_id}"

def get_landsat_collection_info(year):
    """Retorna informações sobre a coleção Landsat para o ano"""
    if year <= 2011:
        return {
            'collection': 'LANDSAT/LT05/C02/T1_L2',
            'satellite': 'Landsat 5 (TM)',
            'bands': {'swir1': 'SR_B5', 'nir': 'SR_B4', 'red': 'SR_B3'}
        }
    elif year <= 2013:
        return {
            'collection': 'LANDSAT/LE07/C02/T1_L2',
            'satellite': 'Landsat 7 (ETM+)',
            'bands': {'swir1': 'SR_B5', 'nir': 'SR_B4', 'red': 'SR_B3'}
        }
    elif year >= 2021:
        return {
            'collection': 'LANDSAT/LC08/C02/T1_L2 + LANDSAT/LC09/C02/T1_L2',
            'satellite': 'Landsat 8/9 (OLI)',
            'bands': {'swir1': 'SR_B6', 'nir': 'SR_B5', 'red': 'SR_B4'}
        }
    else:
        return {
            'collection': 'LANDSAT/LC08/C02/T1_L2',
            'satellite': 'Landsat 8 (OLI)',
            'bands': {'swir1': 'SR_B6', 'nir': 'SR_B5', 'red': 'SR_B4'}
        }

def log_message(message, level='INFO'):
    """Registra mensagens de log"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] [Mosaic Clipper] {message}")
