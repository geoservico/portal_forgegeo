# -*- coding: utf-8 -*-
"""
MapBiomas Handler
Modulo para acesso direto aos dados MapBiomas via Google Cloud Storage.
Sem necessidade de autenticacao - acesso publico.
Usa GDAL /vsicurl/ para recortar remotamente sem baixar o arquivo inteiro.
"""

import os
import tempfile
import json
import time
import random
from pathlib import Path
from typing import List, Optional, Callable, Dict

from qgis.core import (
    QgsGeometry,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsField,
    QgsFeature,
    QgsWkbTypes,
    QgsRasterLayer,
    QgsPalettedRasterRenderer,
    QgsColorRampShader,
    QgsSingleBandPseudoColorRenderer,
    QgsRasterShader,
    QgsRasterTransparency,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsSymbol,
    QgsDistanceArea
)
from PyQt5.QtGui import QColor

try:
    from qgis import processing
    PROCESSING_AVAILABLE = True
except ImportError:
    PROCESSING_AVAILABLE = False

try:
    from osgeo import gdal
    GDAL_AVAILABLE = True
except ImportError:
    GDAL_AVAILABLE = False


class EarthEngineHandler:
    """Gerenciador de acesso ao MapBiomas via Google Cloud Storage (acesso publico)"""

    # URL base validada e testada
    MAPBIOMAS_BASE_URL = (
        'https://storage.googleapis.com/mapbiomas-public'
        '/initiatives/brasil/collection_{collection}'
        '/lulc/coverage/brazil_coverage_{year}.tif'
    )

    DEFAULT_COLLECTION = 10
    AVAILABLE_YEARS = list(range(1985, 2025))

    # Legenda MapBiomas Collection 10 com cores (RGB)
    MAPBIOMAS_PALETTE = {
        3:  {'name': 'Formação Florestal', 'color': (31, 141, 73)},
        4:  {'name': 'Formação Savânica', 'color': (125, 201, 117)},
        5:  {'name': 'Mangue', 'color': (240, 67, 129)},
        6:  {'name': 'Floresta Alagável', 'color': (0, 119, 133)},
        49: {'name': 'Restinga Arbórea', 'color': (2, 214, 89)},
        10: {'name': 'Vegetação Herbácea e Arbustiva', 'color': (214, 188, 116)},
        11: {'name': 'Área Úmida', 'color': (81, 151, 153)},
        12: {'name': 'Formação Campestre', 'color': (214, 188, 116)},
        32: {'name': 'Apicum', 'color': (252, 129, 20)},
        29: {'name': 'Afloramento Rochoso', 'color': (255, 170, 95)},
        50: {'name': 'Restinga Herbácea', 'color': (173, 81, 0)},
        15: {'name': 'Pastagem', 'color': (237, 222, 142)},
        39: {'name': 'Soja', 'color': (245, 179, 200)},
        20: {'name': 'Cana-de-Açúcar', 'color': (219, 112, 147)},
        40: {'name': 'Arroz', 'color': (199, 21, 133)},
        62: {'name': 'Algodão', 'color': (255, 105, 180)},
        41: {'name': 'Outras Lavouras Temporárias', 'color': (245, 194, 201)},
        46: {'name': 'Café', 'color': (214, 143, 226)},
        47: {'name': 'Citrus', 'color': (153, 50, 204)},
        35: {'name': 'Dendê', 'color': (144, 101, 208)},
        48: {'name': 'Outras Lavouras Perenes', 'color': (230, 204, 255)},
        9:  {'name': 'Silvicultura', 'color': (122, 89, 0)},
        21: {'name': 'Mosaico de Usos', 'color': (255, 239, 195)},
        23: {'name': 'Praia, Duna e Areal', 'color': (255, 160, 122)},
        24: {'name': 'Área Urbanizada', 'color': (212, 39, 30)},
        30: {'name': 'Mineração', 'color': (156, 0, 39)},
        75: {'name': 'Usina Fotovoltaica', 'color': (226, 17, 0)},
        25: {'name': 'Outras Áreas não Vegetadas', 'color': (219, 77, 79)},
        33: {'name': 'Rio, Lago e Oceano', 'color': (37, 50, 228)},
        31: {'name': 'Aquicultura', 'color': (9, 16, 119)},
        27: {'name': 'Não observado', 'color': (255, 255, 255)},
    }

    def __init__(self, credentials_path=None):
        self.authenticated = True
        self.available_years = self.AVAILABLE_YEARS
        self.last_error = None

    def get_available_years(self):
        return self.available_years

    def _get_url(self, year, collection=None):
        col = collection or self.DEFAULT_COLLECTION
        return self.MAPBIOMAS_BASE_URL.format(collection=col, year=year)

    def clip_mapbiomas(self, geometries, year, output_path,
                       progress_callback=None, collection=None):
        """Recorta a imagem MapBiomas via GDAL /vsicurl/"""
        temp_mask_path = None
        try:
            if not geometries:
                raise ValueError("Nenhuma geometria fornecida")
            if year not in self.AVAILABLE_YEARS:
                raise ValueError(f"Ano {year} indisponivel.")
            
            if progress_callback: progress_callback(5)

            url = self._get_url(year, collection)
            vsicurl_path = f'/vsicurl/{url}'

            temp_dir = tempfile.gettempdir()
            # Usar nome unico para evitar erro de arquivo em uso
            unique_id = int(time.time()) + random.randint(1, 1000)
            temp_mask_path = os.path.join(temp_dir, f'geos_clip_mask_{unique_id}.shp')
            self._create_mask_layer(geometries, temp_mask_path)

            if progress_callback: progress_callback(20)

            params = {
                'INPUT': vsicurl_path,
                'MASK': temp_mask_path,
                'NODATA': 0,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OPTIONS': 'COMPRESS=LZW',
                'OUTPUT': output_path,
            }
            processing.run('gdal:cliprasterbymasklayer', params)

            if progress_callback: progress_callback(100)
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False
        finally:
            if temp_mask_path:
                for ext in ('.shp', '.shx', '.dbf', '.prj', '.cpg'):
                    p = temp_mask_path.replace('.shp', ext)
                    if os.path.exists(p):
                        try: os.remove(p)
                        except: pass

    def _create_mask_layer(self, geometries, output_path):
        from qgis.core import QgsFields
        crs = QgsCoordinateReferenceSystem('EPSG:4326')
        geom_type = QgsWkbTypes.MultiPolygon if geometries[0].isMultipart() else QgsWkbTypes.Polygon
        fields = QgsFields()
        fields.append(QgsField('id', 4))
        writer = QgsVectorFileWriter(output_path, 'UTF-8', fields, geom_type, crs, 'ESRI Shapefile')
        for i, geom in enumerate(geometries):
            feat = QgsFeature(fields)
            feat.setGeometry(geom)
            feat.setAttributes([i])
            writer.addFeature(feat)
        del writer

    def apply_mapbiomas_symbology(self, layer: QgsRasterLayer):
        """Aplica a paleta de cores e nomes das classes do MapBiomas ao raster"""
        provider = layer.dataProvider()
        classes = []
        for val, info in self.MAPBIOMAS_PALETTE.items():
            color = QColor(*info['color'])
            classes.append(QgsPalettedRasterRenderer.Class(val, color, info['name']))
        
        renderer = QgsPalettedRasterRenderer(provider, 1, classes)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def polygonize_and_calculate_areas(self, raster_path: str, output_vector_path: str):
        """Vetoriza, dissolve por classe e calcula as áreas totais na tabela de atributos"""
        temp_poly_path = None
        try:
            temp_dir = tempfile.gettempdir()
            # Usar nome unico para evitar erro de arquivo em uso
            unique_id = int(time.time()) + random.randint(1, 1000)
            temp_poly_path = os.path.join(temp_dir, f'temp_poly_raw_{unique_id}.gpkg')

            # 1. Poligonizar (GDAL)
            params_poly = {
                'INPUT': raster_path,
                'BAND': 1,
                'FIELD': 'class',
                'EIGHT_CONNECTEDNESS': False,
                'OUTPUT': temp_poly_path
            }
            processing.run('gdal:polygonize', params_poly)

            # 2. Dissolver por classe (para consolidar a tabela)
            params_dissolve = {
                'INPUT': temp_poly_path,
                'FIELD': ['class'],
                'OUTPUT': output_vector_path
            }
            processing.run('native:dissolve', params_dissolve)

            # 3. Carregar o vetor consolidado
            layer = QgsVectorLayer(output_vector_path, "MapBiomas Vetor", "ogr")
            if not layer.isValid():
                return False

            # 4. Adicionar campos
            layer.startEditing()
            layer.addAttribute(QgsField("class_name", 10)) # String
            layer.addAttribute(QgsField("area_ha", 6, "double", 10, 2)) # Double
            layer.updateFields()

            idx_class = layer.fields().indexFromName('class')
            idx_name = layer.fields().indexFromName('class_name')
            idx_area = layer.fields().indexFromName('area_ha')

            # 5. Calcular áreas e nomes
            d = QgsDistanceArea()
            d.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
            d.setEllipsoid(QgsProject.instance().ellipsoid())

            for feat in layer.getFeatures():
                class_val = int(feat.attributes()[idx_class])
                name = self.MAPBIOMAS_PALETTE.get(class_val, {}).get('name', f'Classe {class_val}')
                
                geom = feat.geometry()
                area_m2 = d.measureArea(geom)
                area_ha = area_m2 / 10000.0

                layer.changeAttributeValue(feat.id(), idx_name, name)
                layer.changeAttributeValue(feat.id(), idx_area, area_ha)

            layer.commitChanges()
            return True
        except Exception as e:
            print(f"Erro na vetorização/dissolução: {e}")
            return False
        finally:
            # Tentar limpar o arquivo temporario
            if temp_poly_path and os.path.exists(temp_poly_path):
                try:
                    # Forcar liberacao do objeto se existir
                    if 'layer_temp' in locals(): del layer_temp
                    os.remove(temp_poly_path)
                except:
                    pass

    def apply_vector_symbology(self, layer: QgsVectorLayer):
        """Aplica a simbologia categorizada ao vetor com as cores do MapBiomas"""
        categories = []
        idx_class = layer.fields().indexFromName('class')
        unique_values = layer.uniqueValues(idx_class)
        
        for val in sorted(unique_values):
            info = self.MAPBIOMAS_PALETTE.get(int(val), {'name': f'Classe {val}', 'color': (200, 200, 200)})
            color = QColor(*info['color'])
            
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(color)
            symbol.setOpacity(0.8)
            
            category = QgsRendererCategory(val, symbol, info['name'])
            categories.append(category)
            
        renderer = QgsCategorizedSymbolRenderer('class', categories)
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def get_area_summary(self, vector_path: str) -> Dict[str, float]:
        """Calcula a soma das áreas por classe"""
        summary = {}
        layer = QgsVectorLayer(vector_path, "temp", "ogr")
        if not layer.isValid():
            return summary
            
        idx_name = layer.fields().indexFromName('class_name')
        idx_area = layer.fields().indexFromName('area_ha')
        
        for feat in layer.getFeatures():
            name = feat.attributes()[idx_name]
            area = feat.attributes()[idx_area]
            summary[name] = summary.get(name, 0.0) + area
            
        return summary
