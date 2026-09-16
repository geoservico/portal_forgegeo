# -*- coding: utf-8 -*-
"""
Processing Provider - Integração com QGIS Processing Framework
Permite usar o plugin como algoritmo no Processing
"""

from qgis.core import (
    QgsProcessingProvider, QgsProcessingAlgorithm, QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber, QgsProcessingParameterFile, QgsProcessingOutputRasterLayer,
    QgsProcessingContext, QgsProcessingFeedback, QgsRasterLayer, QgsProject
)
from qgis.PyQt.QtGui import QIcon
import os


class GeoServicioClipperProvider(QgsProcessingProvider):
    """Provider de processamento para GeoServiço-CLIPPER"""
    
    def __init__(self):
        super().__init__()
        self.ee_handler = None
    
    def loadAlgorithms(self):
        """Carregar algoritmos do provider"""
        self.addAlgorithm(MapBiomasClipAlgorithm(self.ee_handler))
    
    def id(self):
        """ID único do provider"""
        return 'geosservico_clipper'
    
    def name(self):
        """Nome do provider"""
        return 'GeoServiço-CLIPPER'
    
    def icon(self):
        """Ícone do provider"""
        plugin_dir = os.path.dirname(__file__)
        icon_path = os.path.join(plugin_dir, 'icon.png')
        return QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
    
    def longName(self):
        """Nome longo do provider"""
        return 'GeoServiço-CLIPPER - Recortar MapBiomas'


class MapBiomasClipAlgorithm(QgsProcessingAlgorithm):
    """Algoritmo para recortar MapBiomas"""
    
    # Constantes para parâmetros
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_YEAR = 'INPUT_YEAR'
    INPUT_COLLECTION = 'INPUT_COLLECTION'
    OUTPUT_RASTER = 'OUTPUT_RASTER'
    
    def __init__(self, ee_handler=None):
        super().__init__()
        self.ee_handler = ee_handler
    
    def createInstance(self):
        """Criar nova instância do algoritmo"""
        return MapBiomasClipAlgorithm(self.ee_handler)
    
    def name(self):
        """Nome do algoritmo"""
        return 'mapbiomas_clip'
    
    def displayName(self):
        """Nome para exibição"""
        return 'Recortar MapBiomas'
    
    def group(self):
        """Grupo do algoritmo"""
        return 'MapBiomas'
    
    def groupId(self):
        """ID do grupo"""
        return 'mapbiomas'
    
    def shortHelpString(self):
        """Texto de ajuda curto"""
        return (
            'Recorta imagens MapBiomas usando uma camada vetorial como máscara.\n\n'
            'Entrada: Camada vetorial (máscara)\n'
            'Saída: Imagem MapBiomas recortada (GeoTIFF)\n\n'
            'Requer autenticação no Google Earth Engine.'
        )
    
    def initAlgorithm(self, config=None):
        """Inicializar parâmetros do algoritmo"""
        
        # Parâmetro: Camada vetorial de entrada
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                'Camada Vetorial (Máscara)',
                types=[0]  # Apenas camadas vetoriais
            )
        )
        
        # Parâmetro: Ano
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_YEAR,
                'Ano',
                type=1,  # Integer
                defaultValue=2024,
                minValue=1985,
                maxValue=2024
            )
        )
        
        # Parâmetro: Coleção
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INPUT_COLLECTION,
                'Coleção MapBiomas',
                type=1,  # Integer
                defaultValue=10,
                minValue=8,
                maxValue=10
            )
        )
        
        # Parâmetro de saída
        self.addParameter(
            QgsProcessingParameterFile(
                self.OUTPUT_RASTER,
                'Arquivo de Saída',
                fileFilter='GeoTIFF (*.tif);;Todos os arquivos (*.*)'
            )
        )
    
    def processAlgorithm(self, parameters, context, feedback):
        """Executar o algoritmo"""
        
        # Obter parâmetros
        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        year = self.parameterAsInt(parameters, self.INPUT_YEAR, context)
        collection = self.parameterAsInt(parameters, self.INPUT_COLLECTION, context)
        output_path = self.parameterAsFile(parameters, self.OUTPUT_RASTER, context)
        
        # Validações
        if not input_layer or not input_layer.isValid():
            return {self.OUTPUT_RASTER: None}
        
        if not self.ee_handler:
            feedback.reportError('Earth Engine Handler não disponível')
            return {self.OUTPUT_RASTER: None}
        
        try:
            feedback.pushInfo(f'Iniciando recorte para o ano {year}...')
            
            # Obter geometrias
            features = input_layer.getFeatures()
            geometries = [feature.geometry() for feature in features]
            
            if not geometries:
                feedback.reportError('Nenhuma geometria encontrada na camada')
                return {self.OUTPUT_RASTER: None}
            
            feedback.pushInfo(f'Geometrias encontradas: {len(geometries)}')
            
            # Processar recorte
            def progress_callback(value):
                feedback.setProgress(value)
            
            success = self.ee_handler.clip_mapbiomas(
                geometries=geometries,
                year=year,
                output_path=output_path,
                progress_callback=progress_callback
            )
            
            if success:
                feedback.pushInfo('Recorte concluído com sucesso!')
                
                # Carregar resultado
                result_layer = QgsRasterLayer(output_path, f'MapBiomas {year}')
                if result_layer.isValid():
                    QgsProject.instance().addMapLayer(result_layer)
                    feedback.pushInfo(f'Camada adicionada ao projeto')
                
                return {self.OUTPUT_RASTER: output_path}
            else:
                feedback.reportError('Falha ao processar recorte')
                return {self.OUTPUT_RASTER: None}
        
        except Exception as e:
            feedback.reportError(f'Erro: {str(e)}')
            return {self.OUTPUT_RASTER: None}
