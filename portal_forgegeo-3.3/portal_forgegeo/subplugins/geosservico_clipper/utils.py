# -*- coding: utf-8 -*-
"""
Utilitários - Funções auxiliares para o plugin GeoServiço-CLIPPER
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional


def get_plugin_path() -> str:
    """
    Obter caminho do diretório do plugin
    
    Returns:
        Caminho absoluto do diretório do plugin
    """
    return os.path.dirname(os.path.abspath(__file__))


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Configurar logger para o plugin
    
    Args:
        name: Nome do logger
        level: Nível de logging
        
    Returns:
        Instância do logger configurado
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formato das mensagens
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Adicionar handler ao logger
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger


def validate_vector_layer(layer) -> bool:
    """
    Validar se a camada é um vetor válido
    
    Args:
        layer: Camada QGIS
        
    Returns:
        True se válido, False caso contrário
    """
    
    if layer is None:
        return False
    
    try:
        from qgis.core import QgsVectorLayer
        
        if not isinstance(layer, QgsVectorLayer):
            return False
        
        if not layer.isValid():
            return False
        
        if layer.featureCount() == 0:
            return False
        
        return True
    except Exception as e:
        print(f"Erro ao validar camada vetorial: {str(e)}")
        return False


def get_layer_extent(layer) -> Optional[dict]:
    """
    Obter extensão de uma camada
    
    Args:
        layer: Camada QGIS
        
    Returns:
        Dicionário com xmin, ymin, xmax, ymax ou None
    """
    
    try:
        extent = layer.extent()
        
        return {
            'xmin': extent.xMinimum(),
            'ymin': extent.yMinimum(),
            'xmax': extent.xMaximum(),
            'ymax': extent.yMaximum()
        }
    except Exception as e:
        print(f"Erro ao obter extensão da camada: {str(e)}")
        return None


def get_layer_crs(layer) -> Optional[str]:
    """
    Obter CRS de uma camada
    
    Args:
        layer: Camada QGIS
        
    Returns:
        String com código EPSG (ex: 'EPSG:4326') ou None
    """
    
    try:
        crs = layer.crs()
        
        if crs.isValid():
            return crs.authid()
        
        return None
    except Exception as e:
        print(f"Erro ao obter CRS da camada: {str(e)}")
        return None


def reproject_geometry(geometry, source_crs, target_crs):
    """
    Reprojetar geometria entre CRS
    
    Args:
        geometry: Geometria QgsGeometry
        source_crs: CRS de origem (QgsCoordinateReferenceSystem ou string EPSG)
        target_crs: CRS de destino (QgsCoordinateReferenceSystem ou string EPSG)
        
    Returns:
        Geometria reprojetada ou None
    """
    
    try:
        from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
        
        # Converter strings EPSG para QgsCoordinateReferenceSystem se necessário
        if isinstance(source_crs, str):
            source_crs = QgsCoordinateReferenceSystem(source_crs)
        
        if isinstance(target_crs, str):
            target_crs = QgsCoordinateReferenceSystem(target_crs)
        
        # Criar transformação
        transform = QgsCoordinateTransform(
            source_crs,
            target_crs,
            QgsProject.instance()
        )
        
        # Transformar geometria
        geometry.transform(transform)
        
        return geometry
    except Exception as e:
        print(f"Erro ao reprojetar geometria: {str(e)}")
        return None


def create_temp_file(suffix: str = '.tif') -> str:
    """
    Criar arquivo temporário
    
    Args:
        suffix: Sufixo do arquivo
        
    Returns:
        Caminho do arquivo temporário
    """
    
    import tempfile
    
    try:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path
    except Exception as e:
        print(f"Erro ao criar arquivo temporário: {str(e)}")
        return None


def remove_temp_file(file_path: str) -> bool:
    """
    Remover arquivo temporário
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        True se removido com sucesso, False caso contrário
    """
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Erro ao remover arquivo: {str(e)}")
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Formatar tamanho de arquivo em bytes para string legível
    
    Args:
        size_bytes: Tamanho em bytes
        
    Returns:
        String formatada (ex: "2.5 MB")
    """
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} TB"


def is_valid_year(year: int) -> bool:
    """
    Validar se o ano está dentro do intervalo disponível
    
    Args:
        year: Ano
        
    Returns:
        True se válido, False caso contrário
    """
    
    return 1985 <= year <= 2024


def get_mapbiomas_legend() -> dict:
    """
    Obter legenda de classificação MapBiomas Collection 10
    
    Returns:
        Dicionário com valores de classe e descrições
    """
    
    return {
        0: 'Não Observado',
        1: 'Floresta Natural',
        2: 'Floresta Natural',
        3: 'Formação Florestal',
        4: 'Formação Savânica',
        5: 'Manguezal',
        6: 'Floresta Inundável',
        9: 'Plantação Florestal',
        11: 'Área Úmida',
        12: 'Pastagem Natural',
        13: 'Outras Formações Não Florestais',
        15: 'Pastagem',
        18: 'Agricultura',
        20: 'Cana-de-Açúcar',
        21: 'Mosaico de Usos',
        22: 'Área Não Vegetada',
        23: 'Praia, Duna e Mancha de Areia',
        24: 'Área Urbana',
        25: 'Outras Áreas Não Vegetadas',
        29: 'Afloramento Rochoso',
        30: 'Mineração',
        31: 'Aquicultura',
        32: 'Planície de Maré Hipersalina',
        33: 'Rios, Lagos e Oceano',
        34: 'Geleira',
        39: 'Soja',
        40: 'Arroz',
        41: 'Outras Culturas Temporárias',
        46: 'Café',
        47: 'Citrus',
        48: 'Outras Culturas Perenes',
        49: 'Vegetação de Banco de Areia Lenhosa',
        50: 'Vegetação de Banco de Areia Herbácea',
        61: 'Salina',
        62: 'Algodão',
        69: 'Recifes de Coral',
        75: 'Usina Solar Fotovoltaica',
    }
