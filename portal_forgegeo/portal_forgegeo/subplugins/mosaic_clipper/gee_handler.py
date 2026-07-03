import os
import json
# Patch para o erro 'cannot import name discovery_cache from googleapiclient'
try:
    import googleapiclient
    if not hasattr(googleapiclient, 'discovery_cache'):
        import sys
        from types import ModuleType
        mock_cache = ModuleType('googleapiclient.discovery_cache')
        mock_cache.autodetect = lambda: None
        sys.modules['googleapiclient.discovery_cache'] = mock_cache
except ImportError:
    pass
import ee
import tempfile
import urllib.request
from pathlib import Path
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

class GEEHandler:
    def __init__(self):
        self.authenticated = False
        self.credentials_path = Path.home() / '.config' / 'earthengine' / 'credentials'
        self.project_id = None
        # Definir pasta de downloads padrão do usuário
        self.download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ForgeGeo_Mosaics")
        if not os.path.exists(self.download_dir):
            try:
                os.makedirs(self.download_dir)
            except:
                self.download_dir = tempfile.gettempdir()

    def authenticate(self, project_id):
        """Autentica com Google Earth Engine"""
        try:
            self.project_id = project_id
            if self.is_authenticated():
                ee.Initialize(project=project_id)
                self.authenticated = True
                return True
            ee.Authenticate()
            ee.Initialize(project=project_id)
            self.authenticated = True
            return True
        except Exception as e:
            raise Exception(f"Erro na autenticacao GEE: {str(e)}")

    def is_authenticated(self):
        return self.credentials_path.exists()

    def list_projects(self):
        """Lista projetos do Google Cloud associados a conta"""
        try:
            import google.auth
            from googleapiclient import discovery
            credentials, _ = google.auth.default()
            service = discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
            request = service.projects().list()
            response = request.execute()
            projects = [p['projectId'] for p in response.get('projects', [])]
            return projects
        except:
            return []

    def qgis_to_ee_geometry(self, qgis_geometry, source_crs):
        """Converte geometria QGIS para EE Geometry (sempre em WGS84)"""
        try:
            # Reprojetar para WGS84 (EPSG:4326) se necessario
            wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
            # Criar uma copia da geometria para nao alterar a original da camada
            geom_copy = qgis_geometry.__class__(qgis_geometry)
            if source_crs != wgs84:
                transform = QgsCoordinateTransform(source_crs, wgs84, QgsProject.instance())
                geom_copy.transform(transform)

            coords = []
            if geom_copy.isMultipart():
                polygons = geom_copy.asMultiPolygon()
                if polygons:
                    # Pega o primeiro anel do primeiro poligono
                    for point in polygons[0][0]:
                        coords.append([point.x(), point.y()])
            else:
                poly_rings = geom_copy.asPolygon()
                if poly_rings:
                    for point in poly_rings[0]:
                        coords.append([point.x(), point.y()])

            if not coords:
                for vertex in geom_copy.vertices():
                    coords.append([vertex.x(), vertex.y()])

            if not coords or len(coords) < 3:
                raise Exception("Geometria invalida ou vazia")

            if coords[0] != coords[-1]:
                coords.append(coords[0])

            return ee.Geometry.Polygon(coords)
        except Exception as e:
            raise Exception(f"Erro ao converter geometria: {str(e)}")

    def get_collection(self, ano):
        """Retorna a colecao Landsat apropriada para o ano"""
        ini = ee.Date.fromYMD(ano, 1, 1)
        fim = ee.Date.fromYMD(ano, 12, 31)
        if ano <= 2011:
            col = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")
        elif ano <= 2013:
            col = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
        else:
            col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        return col.filterDate(ini, fim)

    def get_best_image(self, collection, geometry):
        """Retorna a melhor imagem da colecao"""
        filtered = collection.filterBounds(geometry)
        if filtered.size().getInfo() == 0:
            return None
        return ee.Image(filtered.sort("CLOUD_COVER").first())

    def process_landsat_image(self, image, ano):
        """Processa a imagem Landsat para falsa cor"""
        scaled = image.multiply(0.0000275).add(-0.2).clamp(0, 1)
        if ano <= 2013:
            return scaled.select(['SR_B5', 'SR_B4', 'SR_B3'])
        else:
            return scaled.select(['SR_B6', 'SR_B5', 'SR_B4'])

    def download_image(self, image, geometry, filename, scale=30):
        """Baixa a imagem recortada localmente"""
        try:
            output_path = os.path.join(self.download_dir, f"{filename}.tif")
            
            # Forcar float32 e recortar
            clipped = image.clip(geometry).toFloat()
            
            # Gerar URL de download
            url = clipped.getDownloadURL({
                'region': geometry,
                'scale': scale,
                'format': 'GEO_TIFF'
            })
            
            # Download usando urllib
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            
            local_file, headers = urllib.request.urlretrieve(url, output_path)
            
            # Verificar se o arquivo realmente existe e tem tamanho > 0
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            else:
                raise Exception("Arquivo baixado esta vazio ou nao foi criado.")
                
        except Exception as e:
            if "too many pixels" in str(e).lower():
                return self.download_image(image, geometry, filename, scale=scale*2)
            raise Exception(f"Erro no download: {str(e)}")
