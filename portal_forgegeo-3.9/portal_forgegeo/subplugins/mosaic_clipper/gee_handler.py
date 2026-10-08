import os
import tempfile
import urllib.request
from pathlib import Path

# Compatibilidade com algumas versões do google-api-python-client.
try:
    import googleapiclient
    if not hasattr(googleapiclient, "discovery_cache"):
        import sys
        from types import ModuleType

        mock_cache = ModuleType("googleapiclient.discovery_cache")
        mock_cache.autodetect = lambda: None
        sys.modules["googleapiclient.discovery_cache"] = mock_cache
except ImportError:
    pass

import ee
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
)


class GEEHandler:
    """Integração do Mosaic Clipper com o Google Earth Engine.

    O fluxo seleciona uma única cena por ano. Não aplica máscaras QA, de nuvem,
    sombra, cirrus, neve, saturação ou falhas SLC; a melhoria visual ocorre
    somente no stretch por percentis, gamma, saturação leve e conversão para
    UInt8 antes do recorte e download.
    """

    START_YEAR = 2000
    END_YEAR = 2027
    SPOT_START_YEAR = 2007
    SPOT_END_YEAR = 2009
    SENTINEL_START_YEAR = 2017
    SENTINEL_END_YEAR = 2027
    SENTINEL_CANDIDATES = 24
    SCALE = 30
    SPOT_SCALE = 20
    SENTINEL_SCALE = 10
    SPOT_COLLECTION = "AIRBUS/SPOT_2_4_5/BRAZIL/2007_2009/MS/V1"
    SENTINEL_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
    BUFFER_ANALYSIS = 20
    LOWER_PERCENTILE = 2
    UPPER_PERCENTILE = 98
    GAMMA = 1.1
    SATURATION = 1.08
    COVERAGE_WEIGHT = 0.90
    CLOUD_WEIGHT = 0.10
    MAX_METADATA_CLOUD = 100
    # Valor fora da faixa visual [0, 255]. Será gravado como NoData no TIFF,
    # evitando que áreas sem observação apareçam como manchas pretas.
    NODATA = -9999
    GAP_FILL_ENABLED = True
    GAP_FILL_SPATIAL_ENABLED = True
    GAP_FILL_SPATIAL_RADIUS = 1
    GAP_FILL_ADJACENT_YEARS = True

    def __init__(self):
        self.authenticated = False
        self.credentials_path = Path.home() / ".config" / "earthengine" / "credentials"
        self.project_id = None
        self.download_dir = os.path.join(
            os.path.expanduser("~"), "Downloads", "ForgeGeo_Mosaics"
        )
        try:
            os.makedirs(self.download_dir, exist_ok=True)
        except OSError:
            self.download_dir = tempfile.gettempdir()

    def authenticate(self, project_id):
        """Autentica e inicializa o Earth Engine com o projeto informado."""
        try:
            if not project_id:
                raise ValueError("Informe o ID de um projeto Google Cloud.")
            self.project_id = project_id
            if not self.is_authenticated():
                ee.Authenticate()
            ee.Initialize(project=project_id)
            self.authenticated = True
            return True
        except Exception as exc:
            raise Exception(f"Erro na autenticacao GEE: {exc}") from exc

    def is_authenticated(self):
        return self.credentials_path.exists()

    def list_projects(self):
        """Lista projetos Google Cloud disponíveis para a conta autenticada."""
        try:
            import google.auth
            from googleapiclient import discovery

            credentials, _ = google.auth.default()
            service = discovery.build(
                "cloudresourcemanager", "v1", credentials=credentials
            )
            response = service.projects().list().execute()
            return [project["projectId"] for project in response.get("projects", [])]
        except Exception:
            return []

    def qgis_to_ee_geometry(self, qgis_geometry, source_crs):
        """Converte uma geometria QGIS para um polígono Earth Engine em WGS84."""
        try:
            wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
            geom_copy = qgis_geometry.__class__(qgis_geometry)
            if source_crs != wgs84:
                transform = QgsCoordinateTransform(
                    source_crs, wgs84, QgsProject.instance()
                )
                geom_copy.transform(transform)

            coords = []
            if geom_copy.isMultipart():
                polygons = geom_copy.asMultiPolygon()
                if polygons and polygons[0]:
                    coords = [[point.x(), point.y()] for point in polygons[0][0]]
            else:
                rings = geom_copy.asPolygon()
                if rings:
                    coords = [[point.x(), point.y()] for point in rings[0]]

            if not coords:
                coords = [[vertex.x(), vertex.y()] for vertex in geom_copy.vertices()]
            if len(coords) < 3:
                raise ValueError("Geometria invalida ou vazia")
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            return ee.Geometry.Polygon(coords)
        except Exception as exc:
            raise Exception(f"Erro ao converter geometria: {exc}") from exc

    @staticmethod
    def _date_range(year):
        start = ee.Date.fromYMD(int(year), 1, 1)
        end = ee.Date.fromYMD(int(year) + 1, 1, 1)
        return start, end

    @staticmethod
    def _scale_landsat(image):
        """Aplica a escala Collection 2 Level 2 somente às bandas ópticas SR."""
        optical = image.select("SR_B.*").multiply(0.0000275).add(-0.2)
        return image.addBands(optical, overwrite=True)

    def _prepare_landsat_57(self, image):
        original = image
        prepared = self._scale_landsat(image).select(
            ["SR_B5", "SR_B4", "SR_B3"], ["SWIR", "NIR", "RED"]
        )
        return (
            prepared.copyProperties(original, original.propertyNames())
            .set("scene_cloud", original.get("CLOUD_COVER"))
            .set("sensor_name", original.get("SPACECRAFT_ID"))
        )

    def _prepare_landsat_89(self, image):
        original = image
        prepared = self._scale_landsat(image).select(
            ["SR_B6", "SR_B5", "SR_B4"], ["SWIR", "NIR", "RED"]
        )
        return (
            prepared.copyProperties(original, original.propertyNames())
            .set("scene_cloud", original.get("CLOUD_COVER"))
            .set("sensor_name", original.get("SPACECRAFT_ID"))
        )

    def _prepare_spot_45(self, image):
        original = image
        prepared = image.select(["S", "N", "R"], ["SWIR", "NIR", "RED"]).divide(255)
        return (
            prepared.copyProperties(original, original.propertyNames())
            .set("sensor_name", original.get("satellite"))
            .set("scene_cloud", original.get("cloud_cover"))
            .set("spot_composition", "S_N_R")
        )

    def _prepare_spot_2(self, image):
        original = image
        # SPOT 2 não possui SWIR; os canais N/R/G são padronizados para o
        # fluxo visual comum do plugin.
        prepared = image.select(["N", "R", "G"], ["SWIR", "NIR", "RED"]).divide(255)
        return (
            prepared.copyProperties(original, original.propertyNames())
            .set("sensor_name", original.get("satellite"))
            .set("scene_cloud", original.get("cloud_cover"))
            .set("spot_composition", "N_R_G")
        )

    def _prepare_sentinel(self, image):
        original = image
        visual = image.select(
            ["B11", "B8", "B4"], ["SWIR", "NIR", "RED"]
        ).divide(10000)
        scl = image.select("SCL").rename("SCL")
        return (
            visual.addBands(scl)
            .copyProperties(original, original.propertyNames())
            .set("scene_cloud_metadata", original.get("CLOUDY_PIXEL_PERCENTAGE"))
            .set("scene_cloud", original.get("CLOUDY_PIXEL_PERCENTAGE"))
            .set("sensor_name", original.get("SPACECRAFT_NAME"))
            .set("tile_name", original.get("MGRS_TILE"))
            .set("sentinel_prepared", True)
        )

    def get_collection(self, year, geometry=None, sensor="LANDSAT", start=None, end=None):
        """Retorna a coleção anual de Landsat ou SPOT conforme o sensor."""
        start = start or self._date_range(year)[0]
        end = end or self._date_range(year)[1]
        area = geometry.buffer(self.BUFFER_ANALYSIS) if geometry else None
        sensor = (sensor or "LANDSAT").upper()

        if sensor == "SPOT":
            base = ee.ImageCollection(self.SPOT_COLLECTION).filterDate(start, end)
            if area is not None:
                base = base.filterBounds(area)
            spot2 = base.filter(ee.Filter.eq("satellite", "SPOT2")).map(self._prepare_spot_2)
            spot4 = base.filter(ee.Filter.eq("satellite", "SPOT4")).map(self._prepare_spot_45)
            spot5 = base.filter(ee.Filter.eq("satellite", "SPOT5")).map(self._prepare_spot_45)
            return spot2.merge(spot4).merge(spot5)

        if sensor in ("SENTINEL", "SENTINEL-2", "SENTINEL2"):
            collection = ee.ImageCollection(self.SENTINEL_COLLECTION).filterDate(start, end)
            if area is not None:
                collection = collection.filterBounds(area)
            return collection.map(self._prepare_sentinel)

        def base(collection_id):
            collection = ee.ImageCollection(collection_id).filterDate(start, end)
            if area is not None:
                collection = collection.filterBounds(area)
            return collection.filter(ee.Filter.lte("CLOUD_COVER", self.MAX_METADATA_CLOUD))

        landsat5 = base("LANDSAT/LT05/C02/T1_L2").map(self._prepare_landsat_57)
        landsat7 = base("LANDSAT/LE07/C02/T1_L2").map(self._prepare_landsat_57)
        landsat8 = base("LANDSAT/LC08/C02/T1_L2").map(self._prepare_landsat_89)
        landsat9 = base("LANDSAT/LC09/C02/T1_L2").map(self._prepare_landsat_89)
        return landsat5.merge(landsat7).merge(landsat8).merge(landsat9)

    def _add_coverage(self, image, geometry):
        intersection = image.geometry().intersection(geometry, 1)
        image_area = ee.Number(geometry.area(1))
        coverage = (
            ee.Number(intersection.area(1))
            .divide(image_area)
            .multiply(100)
            .min(100)
        )
        return image.set("coverage_percent", coverage)

    def _add_sentinel_cloud(self, image, geometry):
        """Calcula nuvens no imóvel apenas para o ranking Sentinel-2."""
        scl = image.select("SCL")
        cloud = (
            scl.eq(3)
            .Or(scl.eq(8))
            .Or(scl.eq(9))
            .Or(scl.eq(10))
            .Or(scl.eq(11))
            .rename("cloud")
        )
        analysable = scl.neq(0).And(scl.neq(1))
        result = cloud.updateMask(analysable).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=20,
            bestEffort=True,
            maxPixels=1e10,
            tileScale=4,
        )
        cloud_percent = ee.Number(
            ee.Algorithms.If(result.contains("cloud"), result.get("cloud"), 1)
        ).multiply(100)
        return image.set(
            "cloud_percent_aoi", cloud_percent
        ).set("clear_percent_aoi", ee.Number(100).subtract(cloud_percent))

    @staticmethod
    def _add_score(image):
        coverage = ee.Number(image.get("coverage_percent"))
        cloud_property = image.get("scene_cloud")
        cloud = ee.Number(
            ee.Algorithms.If(
                ee.Algorithms.IsEqual(cloud_property, None), 100, cloud_property
            )
        )
        score = coverage.multiply(GEEHandler.COVERAGE_WEIGHT).add(
            ee.Number(100).subtract(cloud).multiply(GEEHandler.CLOUD_WEIGHT)
        )
        return image.set("score", score)

    def get_best_image(self, collection, geometry, sensor="LANDSAT", year=None):
        """Seleciona a melhor cena e preenche apenas pixels sem dados.

        A cena vencedora permanece prioritária. As demais cenas do mesmo
        período só fornecem pixels que estão mascarados na cena vencedora,
        resolvendo falhas SLC/limites de aquisição sem remover nuvens ou
        sombras reais da imagem principal.
        """
        source_collection = ee.ImageCollection(collection)
        collection = source_collection
        sensor = (sensor or "LANDSAT").upper()
        if sensor in ("SENTINEL", "SENTINEL-2", "SENTINEL2"):
            # A coleção Sentinel pode conter dezenas de cenas por ano. O
            # Earth Engine limita agregações simultâneas; por isso, usamos o
            # metadado CLOUDY_PIXEL_PERCENTAGE para pré-selecionar candidatas
            # e calculamos a SCL somente nesse conjunto reduzido.
            collection = collection.sort("CLOUDY_PIXEL_PERCENTAGE", True).limit(
                self.SENTINEL_CANDIDATES
            )
            collection = collection.map(lambda image: self._add_sentinel_cloud(image, geometry))
            ranked = (
                collection.map(lambda image: self._add_coverage(image, geometry))
                .map(lambda image: image.set(
                    "score",
                    ee.Number(image.get("coverage_percent")).multiply(0.70).add(
                        ee.Number(image.get("clear_percent_aoi")).multiply(0.30)
                    )
                ))
                .filter(ee.Filter.gt("coverage_percent", 0))
                .sort("score", False)
            )
        else:
            ranked = (
                collection.map(lambda image: self._add_coverage(image, geometry))
                .map(self._add_score)
                .filter(ee.Filter.gt("coverage_percent", 0))
                .sort("score", False)
            )
        if ranked.size().getInfo() == 0:
            return None
        best = ee.Image(ranked.first())
        if not self.GAP_FILL_ENABLED:
            return best

        # mosaic() usa a última imagem como prioridade. Ordenando da pior
        # para a melhor, a cena vencedora fica no topo e os pixels válidos
        # das cenas anteriores preenchem somente as áreas mascaradas.
        ordered = ranked.sort("score", True)
        gap_filled = ordered.mosaic()
        result = best.unmask(gap_filled)

        # Algumas falhas persistem quando todas as cenas ranqueadas têm a
        # mesma máscara (caso comum em bordas e falhas SLC). O composto
        # temporal usa todos os pixels válidos do período e só é consultado
        # nas áreas ainda vazias; a cena vencedora não é alterada nos demais
        # pixels. Para Sentinel, ranked já contém as candidatas limitadas.
        annual_composite = source_collection.select(
            ["SWIR", "NIR", "RED"]
        ).median()
        result = result.unmask(annual_composite)

        # Para Landsat, cenas dos anos imediatamente anterior e posterior
        # ajudam em falhas que persistem durante todo o ano consultado. Elas
        # só entram nos pixels ainda mascarados e nunca substituem pixels
        # válidos da cena principal ou do composto anual.
        if self.GAP_FILL_ADJACENT_YEARS and year is not None and sensor == "LANDSAT":
            adjacent = []
            for adjacent_year in (int(year) - 1, int(year) + 1):
                if adjacent_year < self.START_YEAR or adjacent_year > self.END_YEAR:
                    continue
                adjacent_collection = self.get_collection(
                    adjacent_year, geometry, sensor
                )
                adjacent.append(adjacent_collection.select(["SWIR", "NIR", "RED"]))
            if adjacent:
                adjacent_composite = ee.ImageCollection(adjacent[0])
                for item in adjacent[1:]:
                    adjacent_composite = adjacent_composite.merge(item)
                result = result.unmask(adjacent_composite.median())

        # Último recurso determinístico: média dos vizinhos válidos, somente
        # onde nem a cena nem o composto temporal têm dados. Isso evita que
        # o GeoTIFF apresente manchas pretas de NoData dentro da parcela,
        # sem inventar valores sobre pixels observados.
        if self.GAP_FILL_SPATIAL_ENABLED:
            spatial = result.focal_mean(
                radius=self.GAP_FILL_SPATIAL_RADIUS,
                kernelType="square",
                units="pixels",
                iterations=2,
            )
            result = result.unmask(spatial)

        return result.copyProperties(best, best.propertyNames()).set(
            "gap_filled", True
        ).set("gap_fill_scene_count", ranked.size())

    def process_landsat_image(self, image, year=None):
        """Aplica o tratamento visual comum a Landsat e SPOT."""
        # O primeiro elemento de uma coleção pode chegar como ee.Element;
        # normalizar aqui garante acesso aos métodos específicos de ee.Image.
        image = ee.Image(image)
        bands = ["SWIR", "NIR", "RED"]
        percentiles = image.select(bands).reduceRegion(
            reducer=ee.Reducer.percentile(
                [self.LOWER_PERCENTILE, self.UPPER_PERCENTILE]
            ),
            geometry=image.geometry(),
            scale=self.SCALE,
            bestEffort=True,
            maxPixels=1e10,
            tileScale=4,
        )
        lower_suffix = f"p{self.LOWER_PERCENTILE}"
        upper_suffix = f"p{self.UPPER_PERCENTILE}"
        minimum = ee.Image.constant(
            [
                ee.Number(percentiles.get(f"SWIR_{lower_suffix}")),
                ee.Number(percentiles.get(f"NIR_{lower_suffix}")),
                ee.Number(percentiles.get(f"RED_{lower_suffix}")),
            ]
        ).rename(bands)
        maximum = ee.Image.constant(
            [
                ee.Number(percentiles.get(f"SWIR_{upper_suffix}")),
                ee.Number(percentiles.get(f"NIR_{upper_suffix}")),
                ee.Number(percentiles.get(f"RED_{upper_suffix}")),
            ]
        ).rename(bands)
        interval = maximum.subtract(minimum).max(0.000001)
        visual = image.select(bands).subtract(minimum).divide(interval).clamp(0, 1)
        visual = visual.pow(ee.Number(1).divide(self.GAMMA))
        mean = visual.reduce(ee.Reducer.mean())
        visual = (
            visual.subtract(mean)
            .multiply(self.SATURATION)
            .add(mean)
            .clamp(0, 1)
        )
        return (
            visual.multiply(255)
            .round()
            .toFloat()
            .rename(bands)
            .copyProperties(image, image.propertyNames())
        )

    @staticmethod
    def get_image_name(image, fallback="Landsat", suffix=""):
        """Gera nome de cena Landsat ou SPOT, com sufixo opcional."""
        try:
            image = ee.Image(image)
            metadata = image.toDictionary(
                [
                    "WRS_PATH", "WRS_ROW", "system:time_start",                     "product_id", "grid_reference", "satellite", "sensor_name", "tile_name"

                ]
            ).getInfo()
            timestamp = metadata.get("system:time_start")
            date = (
                ee.Date(timestamp).format("YYYY-MM-dd").getInfo()
                if timestamp is not None else fallback
            )
            sensor = str(metadata.get("sensor_name") or metadata.get("satellite") or "")
            if sensor.upper().startswith("SPOT"):
                identifier = metadata.get("product_id") or metadata.get("grid_reference") or sensor
                safe_identifier = "".join(
                    char if char.isalnum() or char in "_-" else "_"
                    for char in str(identifier)
                ).strip("_")
                return f"{safe_identifier}_{date}{suffix}"
            if metadata.get("tile_name") or sensor.upper().startswith("SENTINEL"):
                tile = str(metadata.get("tile_name") or "SENTINEL2").replace("None", "SENTINEL2")
                return f"{tile}_{date}{suffix}"
            path = str(metadata.get("WRS_PATH", "000")).zfill(3)
            row = str(metadata.get("WRS_ROW", "000")).zfill(3)
            return f"{path}-{row}_{date}{suffix}"
        except Exception:
            return f"{fallback}{suffix}"

    def download_image(self, image, geometry, filename, scale=None):
        """Baixa GeoTIFF com NoData explícito fora da faixa visual."""
        try:
            # Normalização defensiva: download_image também é usado por versões
            # antigas do diálogo que podem encaminhar um ee.Element.
            image = ee.Image(image)
            output_path = os.path.join(self.download_dir, f"{filename}.tif")
            scale = scale or self.SCALE
            clipped = image.clip(geometry).unmask(self.NODATA).toFloat()
            url = clipped.getDownloadURL(
                {
                    "region": geometry,
                    "scale": scale,
                    "format": "GEO_TIFF",
                    "filePerBand": False,
                    "formatOptions": {"noData": self.NODATA},
                }
            )
            if not url.startswith(("http://", "https://")):
                raise Exception(f"URL invalida ou esquema nao permitido: {url}")
            import requests

            response = requests.get(
                url,
                stream=True,
                timeout=120,
                headers={"User-agent": "Mozilla/5.0"},
            )
            response.raise_for_status()
            with open(output_path, "wb") as output:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        output.write(chunk)
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise Exception("Arquivo baixado esta vazio ou nao foi criado.")
            return output_path
        except Exception as exc:
            if "too many pixels" in str(exc).lower() and (scale or self.SCALE) < 240:
                return self.download_image(
                    image, geometry, filename, scale=(scale or self.SCALE) * 2
                )
            raise Exception(f"Erro no download: {exc}") from exc

    # Compatibilidade com chamadas antigas do plugin.
    def clip_and_export(self, image, geometry, filename, scale=None):
        return self.download_image(image, geometry, filename, scale)

    def get_task_status(self, task_id):
        try:
            return ee.data.getTaskStatus([task_id])[0]
        except Exception as exc:
            return {"state": "UNKNOWN", "error_message": str(exc)}

    def process_sensor_image(self, image, sensor="LANDSAT", year=None):
        """Processa a imagem de qualquer sensor no fluxo visual comum."""
        return self.process_landsat_image(ee.Image(image), year)

    def get_collection_info(self, year, sensor="LANDSAT"):
        sensor = (sensor or "LANDSAT").upper()
        if sensor == "SPOT":
            return "SPOT 2/4/5", ["S", "N", "R"]
        if sensor in ("SENTINEL", "SENTINEL-2", "SENTINEL2"):
            return "Sentinel-2A/2B", ["B11", "B8", "B4"]
        if year <= 2011:
            return "Landsat 5", ["SR_B5", "SR_B4", "SR_B3"]
        if year <= 2013:
            return "Landsat 7", ["SR_B5", "SR_B4", "SR_B3"]
        if year >= 2021:
            return "Landsat 8/9", ["SR_B6", "SR_B5", "SR_B4"]
        return "Landsat 8", ["SR_B6", "SR_B5", "SR_B4"]

    # Mantém o nome antigo utilizado por algumas versões do plugin.
    def get_landsat_collection_info(self, year):
        return self.get_collection_info(year)
