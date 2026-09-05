import os
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                                 QComboBox, QFormLayout, QMessageBox, QHBoxLayout)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer
import ee
from .gee_handler import GEEHandler

class ProcessingThread(QThread):
    """Thread para processar imagens sem bloquear a interface"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str, list)

    def __init__(self, gee_handler, geometry, source_crs, layer_name, years, sensor):
        super().__init__()
        self.gee_handler = gee_handler
        self.geometry = geometry
        self.source_crs = source_crs
        self.layer_name = layer_name
        self.years = years
        self.sensor = sensor
        self.downloaded_files = []

    def run(self):
        try:
            ee_geometry = self.gee_handler.qgis_to_ee_geometry(self.geometry, self.source_crs)
            
            periods = []
            if self.sensor == "SPOT":
                for ano in self.years:
                    if ano < self.gee_handler.SPOT_START_YEAR or ano > self.gee_handler.SPOT_END_YEAR:
                        self.progress.emit(f"SPOT não disponível em {ano}; ano ignorado.")
                        continue
                    if ano == 2008:
                        periods.extend([
                            (ano, ee.Date("2008-01-01"), ee.Date("2008-07-22"), "_ANTES"),
                            (ano, ee.Date("2008-07-22"), ee.Date("2009-01-01"), "_POS"),
                        ])
                    else:
                        periods.append((ano, ee.Date.fromYMD(ano, 1, 1), ee.Date.fromYMD(ano + 1, 1, 1), ""))
            else:
                periods = [
                    (ano, ee.Date.fromYMD(ano, 1, 1), ee.Date.fromYMD(ano + 1, 1, 1), "")
                    for ano in self.years
                ]

            for ano, start_date, end_date, suffix in periods:
                period_label = f"{ano}{suffix}"
                self.progress.emit(f"Processando {self.sensor} {period_label}...")
                collection = self.gee_handler.get_collection(
                    ano, ee_geometry, self.sensor, start_date, end_date
                )
                best_image = self.gee_handler.get_best_image(
                    collection, ee_geometry, self.sensor
                )

                if best_image is None:
                    self.progress.emit(f"⚠ Nenhuma imagem encontrada para {period_label}")
                    continue

                processed_image = self.gee_handler.process_sensor_image(
                    best_image, self.sensor, ano
                )
                img_id = self.gee_handler.get_image_name(
                    best_image, f"IMG_{period_label}", suffix
                )
                nome_final = f"{self.layer_name}_{period_label}_{img_id}"
                self.progress.emit(f"Baixando {nome_final}...")

                try:
                    file_path = self.gee_handler.download_image(
                        processed_image,
                        ee_geometry,
                        nome_final,
                        self.gee_handler.SPOT_SCALE if self.sensor == "SPOT" else (
                            self.gee_handler.SENTINEL_SCALE if self.sensor == "SENTINEL" else self.gee_handler.SCALE
                        )
                    )
                    if file_path:
                        self.downloaded_files.append(file_path)
                        self.progress.emit(f"✓ Arquivo salvo: {file_path}")
                except Exception as e:
                    self.progress.emit(f"✗ Erro ao baixar {nome_final}: {str(e)}")
            
            if self.downloaded_files:
                message = f"✓ Sucesso! {len(self.downloaded_files)} imagem(ns) foram baixadas na pasta Downloads/ForgeGeo_Mosaics."
                self.finished.emit(True, message, self.downloaded_files)
            else:
                message = "✗ Nenhuma imagem foi processada com sucesso."
                self.finished.emit(False, message, [])
                
        except Exception as e:
            self.finished.emit(False, f"✗ Erro fatal: {str(e)}", [])

class MosaicClipperDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mosaic Clipper - Landsat/SPOT/Sentinel-2")
        self.setGeometry(100, 100, 700, 500)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.gee_handler = GEEHandler()
        self.processing_thread = None
        self.setup_ui()

    def setup_ui(self):
        form_layout = QFormLayout()
        
        self.gee_label = QLabel("Google Earth Engine - Autenticação Obrigatória:")
        form_layout.addRow(self.gee_label)
        
        self.project_id_label = QLabel("Projeto Google Cloud:")
        self.project_id_combo = QComboBox()
        self.project_id_combo.setEditable(True)
        self.project_id_combo.setPlaceholderText("Selecione ou digite o ID do projeto")
        
        self.help_project_btn = QPushButton("Não sei meu ID")
        self.help_project_btn.setStyleSheet("font-size: 10px; color: blue; text-decoration: underline; border: none; background: none;")
        self.help_project_btn.clicked.connect(self.open_google_console)
        
        self.fix_perm_btn = QPushButton("Ativar API/Permissões")
        self.fix_perm_btn.setStyleSheet("font-size: 10px; color: darkgreen; text-decoration: underline; border: none; background: none;")
        self.fix_perm_btn.clicked.connect(self.open_permission_fix)
        
        project_h_layout = QHBoxLayout()
        project_h_layout.addWidget(self.project_id_combo)
        project_h_layout.addWidget(self.help_project_btn)
        project_h_layout.addWidget(self.fix_perm_btn)
        form_layout.addRow(self.project_id_label, project_h_layout)
        
        self.auth_button = QPushButton("1. Autenticar / Listar Projetos")
        self.auth_button.clicked.connect(self.authenticate_gee)
        form_layout.addRow(self.auth_button)
        
        self.gee_status_label = QLabel("Status: Não autenticado")
        self.gee_status_label.setStyleSheet("color: gray;")
        form_layout.addRow(self.gee_status_label)
        
        line = QLabel("<hr>")
        form_layout.addRow(line)
        
        self.layer_label = QLabel("2. Selecione a Camada (Máscara):")
        self.layer_combo = QComboBox()
        self.refresh_layers()
        form_layout.addRow(self.layer_label, self.layer_combo)

        self.sensor_label = QLabel("3. Sensor:")
        self.sensor_combo = QComboBox()
        self.sensor_combo.addItem("Landsat 5, 7, 8 e 9", "LANDSAT")
        self.sensor_combo.addItem("SPOT 2, 4 e 5", "SPOT")
        self.sensor_combo.addItem("Sentinel-2A e 2B", "SENTINEL")
        self.sensor_combo.currentIndexChanged.connect(self.update_sensor_years)
        form_layout.addRow(self.sensor_label, self.sensor_combo)
        
        self.year_label = QLabel("4. Período de Anos:")
        year_h_layout = QHBoxLayout()
        self.year_start_combo = QComboBox()
        self.year_end_combo = QComboBox()
        self.update_sensor_years()
        
        year_h_layout.addWidget(QLabel("De:"))
        year_h_layout.addWidget(self.year_start_combo)
        year_h_layout.addWidget(QLabel("Até:"))
        year_h_layout.addWidget(self.year_end_combo)
        form_layout.addRow(self.year_label, year_h_layout)
        
        self.layout.addLayout(form_layout)
        
        self.process_button = QPushButton("4. BAIXAR E CARREGAR NO QGIS")
        self.process_button.setEnabled(False)
        self.process_button.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.process_button.clicked.connect(self.process_images)
        self.layout.addWidget(self.process_button)
        
        self.log_label = QLabel("Log de Processamento:")
        self.layout.addWidget(self.log_label)
        self.log_text = QLabel("Aguardando início...")
        self.log_text.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ccc; padding: 5px;")
        self.log_text.setWordWrap(True)
        self.layout.addWidget(self.log_text)

    def update_sensor_years(self):
        """Atualiza o intervalo de anos conforme a disponibilidade do sensor."""
        current_sensor = self.sensor_combo.currentData() if hasattr(self, "sensor_combo") else "LANDSAT"
        if current_sensor == "SPOT":
            start, end = 2007, 2009
        elif current_sensor == "SENTINEL":
            start, end = 2017, 2027
        else:
            start, end = 2000, 2027
        current_start = self.year_start_combo.currentText() if hasattr(self, "year_start_combo") else ""
        current_end = self.year_end_combo.currentText() if hasattr(self, "year_end_combo") else ""
        self.year_start_combo.blockSignals(True)
        self.year_end_combo.blockSignals(True)
        self.year_start_combo.clear()
        self.year_end_combo.clear()
        years = [str(year) for year in range(start, end + 1)]
        self.year_start_combo.addItems(years)
        self.year_end_combo.addItems(years)
        if current_start in years:
            self.year_start_combo.setCurrentText(current_start)
        else:
            self.year_start_combo.setCurrentText(str(start))
        if current_end in years:
            self.year_end_combo.setCurrentText(current_end)
        else:
            self.year_end_combo.setCurrentText(str(start if current_sensor == "SPOT" else end))
        self.year_start_combo.blockSignals(False)
        self.year_end_combo.blockSignals(False)
        self.year_label.setText(
            f"4. Período de Anos ({start}-{end}):"
        )

    def open_google_console(self):
        QDesktopServices.openUrl(QUrl("https://console.cloud.google.com/projectselector2/home/dashboard"))

    def open_permission_fix(self):
        project_id = self.project_id_combo.currentText().strip()
        if project_id:
            url = f"https://console.cloud.google.com/apis/library/earthengine.googleapis.com?project={project_id}"
            QDesktopServices.openUrl(QUrl(url))

    def refresh_layers(self):
        self.layer_combo.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                self.layer_combo.addItem(layer.name(), layer)

    def authenticate_gee(self):
        project_id = self.project_id_combo.currentText().strip()
        try:
            self.gee_handler.authenticate(project_id)
            projects = self.gee_handler.list_projects()
            if projects:
                self.project_id_combo.clear()
                self.project_id_combo.addItems(projects)
                if project_id in projects:
                    self.project_id_combo.setCurrentText(project_id)
            self.gee_status_label.setText("Status: ✓ Autenticado")
            self.gee_status_label.setStyleSheet("color: green;")
            self.process_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao autenticar: {str(e)}")

    def process_images(self):
        selected_layer = self.layer_combo.currentData()
        if not selected_layer: return
        
        features = selected_layer.getFeatures()
        feature = next(features, None)
        if not feature: return
            
        geometry = feature.geometry()
        source_crs = selected_layer.crs()
        start_year = int(self.year_start_combo.currentText())
        end_year = int(self.year_end_combo.currentText())
        if start_year > end_year:
            QMessageBox.warning(self, "Período inválido", "O ano inicial deve ser menor ou igual ao ano final.")
            return
        sensor = self.sensor_combo.currentData()
        years = list(range(start_year, end_year + 1))
        if sensor == "SPOT" and (start_year < 2007 or end_year > 2009):
            QMessageBox.warning(self, "Período SPOT", "A coleção SPOT está disponível somente de 2007 a 2009.")
            return
        if sensor == "SENTINEL" and (start_year < 2017 or end_year > 2027):
            QMessageBox.warning(self, "Período Sentinel-2", "A coleção Sentinel-2 SR está disponível de 2017 a 2027.")
            return
        
        self.processing_thread = ProcessingThread(
            self.gee_handler, geometry, source_crs, selected_layer.name(), years, sensor
        )
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.start()
        self.process_button.setEnabled(False)

    def update_progress(self, message):
        self.log_text.setText(message)

    def on_processing_finished(self, success, message, downloaded_files):
        self.process_button.setEnabled(True)
        if success:
            QMessageBox.information(self, "Sucesso", message)
            for file_path in downloaded_files:
                if os.path.exists(file_path):
                    layer_name = os.path.basename(file_path).replace('.tif', '')
                    rlayer = QgsRasterLayer(file_path, layer_name)
                    if rlayer.isValid():
                        QgsProject.instance().addMapLayer(rlayer)
        else:
            QMessageBox.critical(self, "Erro", message)
