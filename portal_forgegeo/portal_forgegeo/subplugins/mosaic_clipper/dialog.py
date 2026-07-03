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

    def __init__(self, gee_handler, geometry, source_crs, layer_name, years):
        super().__init__()
        self.gee_handler = gee_handler
        self.geometry = geometry
        self.source_crs = source_crs
        self.layer_name = layer_name
        self.years = years
        self.downloaded_files = []

    def run(self):
        try:
            ee_geometry = self.gee_handler.qgis_to_ee_geometry(self.geometry, self.source_crs)
            
            for ano in self.years:
                self.progress.emit(f"Processando ano {ano}...")
                collection = self.gee_handler.get_collection(ano)
                best_image = self.gee_handler.get_best_image(collection, ee_geometry)
                
                if best_image is None:
                    self.progress.emit(f"⚠ Nenhuma imagem encontrada para {ano}")
                    continue
                
                false_color = self.gee_handler.process_landsat_image(best_image, ano)
                
                try:
                    img_id = best_image.get("LANDSAT_PRODUCT_ID").getInfo()
                except:
                    img_id = f"IMG_{ano}"
                
                nome_final = f"{self.layer_name}_{ano}_{img_id}"
                self.progress.emit(f"Baixando {nome_final}...")
                
                try:
                    file_path = self.gee_handler.download_image(
                        false_color,
                        ee_geometry,
                        nome_final
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
        self.setWindowTitle("Mosaic Clipper - Landsat Download e Carregamento")
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
        
        self.year_label = QLabel("3. Período de Anos (2000-2025):")
        year_h_layout = QHBoxLayout()
        self.year_start_combo = QComboBox()
        self.year_end_combo = QComboBox()
        years = [str(y) for y in range(2000, 2026)]
        self.year_start_combo.addItems(years)
        self.year_end_combo.addItems(years)
        self.year_start_combo.setCurrentText("2023")
        self.year_end_combo.setCurrentText("2023")
        
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
        years = list(range(int(self.year_start_combo.currentText()), int(self.year_end_combo.currentText()) + 1))
        
        self.processing_thread = ProcessingThread(self.gee_handler, geometry, source_crs, selected_layer.name(), years)
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
