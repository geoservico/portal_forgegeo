# -*- coding: utf-8 -*-
"""
Dialog - Interface grafica do plugin GeoServico-CLIPPER
"""

import os
import tempfile
import traceback

from qgis.PyQt.QtCore import Qt, QCoreApplication, QSize, QUrl
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QProgressBar, QTextEdit, QGroupBox, QSpinBox, QMessageBox, QFileDialog,
    QCheckBox, QTabWidget, QWidget
)
from qgis.PyQt.QtGui import QFont, QDesktopServices
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsMapLayerProxyModel, QgsCoordinateReferenceSystem,
    QgsCoordinateTransform
)
from qgis.gui import QgsMapLayerComboBox

# Importar o novo gerador baseado no QGIS Layout
from .report_generator import generate_qgis_pdf_report


class GeoServicioClipperDialog(QDialog):
    """Dialogo principal do plugin GeoServico-CLIPPER"""

    def __init__(self, iface, ee_handler, logger, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface = iface
        self.ee_handler = ee_handler
        self.logger = logger
        self.canvas = iface.mapCanvas()
        
        self.setWindowTitle('GeoServico-CLIPPER - Recortar MapBiomas')
        self.setMinimumSize(580, 620)
        self.setModal(True)

        self.last_raster_path = None
        self.last_vector_path = None
        self.last_year = None
        self.last_layer_name = None

        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout()
        tabs = QTabWidget()

        # ---- Aba Configuracao ----
        cfg = QWidget()
        cfg_lay = QVBoxLayout()

        grp_vec = QGroupBox("Camada Vetorial (Mascara de Recorte)")
        vec_lay = QVBoxLayout()
        vec_lay.addWidget(QLabel("Selecione a camada vetorial:"))
        self.layer_combo = QgsMapLayerComboBox()
        self.layer_combo.setFilters(QgsMapLayerProxyModel.Filter.VectorLayer)
        self.layer_combo.layerChanged.connect(self._on_layer_changed)
        vec_lay.addWidget(self.layer_combo)
        self.lbl_layer_info = QLabel("Nenhuma camada selecionada")
        self.lbl_layer_info.setStyleSheet("color:gray; font-size:10px;")
        vec_lay.addWidget(self.lbl_layer_info)
        grp_vec.setLayout(vec_lay)
        cfg_lay.addWidget(grp_vec)

        grp_mb = QGroupBox("Parametros MapBiomas")
        mb_lay = QVBoxLayout()
        row_year = QHBoxLayout()
        row_year.addWidget(QLabel("Ano:"))
        self.spin_year = QSpinBox()
        self.spin_year.setRange(1985, 2024)
        self.spin_year.setValue(2024)
        row_year.addWidget(self.spin_year)
        row_year.addStretch()
        mb_lay.addLayout(row_year)

        self.chk_vectorize = QCheckBox("Vetorizar, Dissolver e Colorir")
        self.chk_vectorize.setChecked(True)
        mb_lay.addWidget(self.chk_vectorize)
        grp_mb.setLayout(mb_lay)
        cfg_lay.addWidget(grp_mb)

        grp_out = QGroupBox("Arquivo de Saida (Raster)")
        out_lay = QVBoxLayout()
        row_out = QHBoxLayout()
        self.cmb_output = QComboBox()
        self.cmb_output.setEditable(True)
        row_out.addWidget(self.cmb_output)
        btn_browse = QPushButton("Procurar...")
        btn_browse.clicked.connect(self._browse_output)
        row_out.addWidget(btn_browse)
        out_lay.addLayout(row_out)
        grp_out.setLayout(out_lay)
        cfg_lay.addWidget(grp_out)

        cfg_lay.addStretch()
        cfg.setLayout(cfg_lay)
        tabs.addTab(cfg, "Configuracao")

        # ---- Aba Log ----
        log_w = QWidget()
        log_lay = QVBoxLayout()
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_lay.addWidget(self.txt_log)
        log_w.setLayout(log_lay)
        tabs.addTab(log_w, "Log / Resumo")

        main.addWidget(tabs)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main.addWidget(self.progress)

        row_btn = QHBoxLayout()
        self.btn_clip = QPushButton("Recortar MapBiomas")
        self.btn_clip.clicked.connect(self._do_clip)
        self.btn_clip.setStyleSheet("background-color: #1f8d49; color: white; font-weight: bold; height: 30px;")
        row_btn.addWidget(self.btn_clip)
        
        self.btn_report = QPushButton("Gerar Relatorio PDF")
        self.btn_report.clicked.connect(self._generate_pdf)
        self.btn_report.setEnabled(False)
        row_btn.addWidget(self.btn_report)

        btn_cancel = QPushButton("Fechar")
        btn_cancel.clicked.connect(self.reject)
        row_btn.addWidget(btn_cancel)
        main.addLayout(row_btn)
        
        self.setLayout(main)
        self._on_layer_changed()

    def _on_layer_changed(self):
        layer = self.layer_combo.currentLayer()
        if layer:
            self.lbl_layer_info.setText(f"{layer.name()} - {layer.featureCount()} feicao(oes)")
        else:
            self.lbl_layer_info.setText("Nenhuma camada selecionada")

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar recorte", "", "GeoTIFF (*.tif)")
        if path: self.cmb_output.setEditText(path)

    def _log(self, msg):
        self.txt_log.append(msg)
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())
        QCoreApplication.processEvents()

    def _do_clip(self):
        try:
            layer = self.layer_combo.currentLayer()
            if not layer:
                QMessageBox.warning(self, "Aviso", "Selecione uma camada vetorial!")
                return
            
            year = self.spin_year.value()
            out_path = self.cmb_output.currentText().strip()
            if not out_path:
                out_path = os.path.join(tempfile.gettempdir(), f'mapbiomas_{year}_{int(os.times()[4])}.tif')

            self._log(f"--- Iniciando Processo {year} ---")
            geoms = self._get_geometries_4326(layer)
            
            self.progress.setVisible(True)
            self.btn_clip.setEnabled(False)
            
            if self.ee_handler.clip_mapbiomas(geoms, year, out_path, self._update_progress):
                self._log("✓ Raster recortado com sucesso.")
                
                rlayer = QgsRasterLayer(out_path, f"MapBiomas {year} (Raster)")
                if rlayer.isValid():
                    self.ee_handler.apply_mapbiomas_symbology(rlayer)
                    QgsProject.instance().addMapLayer(rlayer)
                    self.last_raster_path = out_path
                
                if self.chk_vectorize.isChecked():
                    self._log("Vetorizando e consolidando areas...")
                    vec_path = out_path.replace('.tif', '_vetor.gpkg')
                    if self.ee_handler.polygonize_and_calculate_areas(out_path, vec_path):
                        vlayer = QgsVectorLayer(vec_path, f"MapBiomas {year} (Vetor)", "ogr")
                        if vlayer.isValid():
                            self.ee_handler.apply_vector_symbology(vlayer)
                            QgsProject.instance().addMapLayer(vlayer)
                            self.last_vector_path = vec_path
                            self.last_year = year
                            self.last_layer_name = layer.name()
                            
                            self._log("\nRESUMO DE AREAS:")
                            summary = self.ee_handler.get_area_summary(vec_path)
                            for name, area in sorted(summary.items(), key=lambda x: x[1], reverse=True):
                                self._log(f"- {name}: {area:.2f} ha")
                            
                            self.btn_report.setEnabled(True)
                            self._log("\n✓ Processo concluido. Relatorio PDF disponivel.")
                
                QMessageBox.information(self, "Sucesso", "Recorte e Vetorizacao concluidos!")
            else:
                QMessageBox.critical(self, "Erro", f"Falha: {self.ee_handler.last_error}")

        except Exception as exc:
            self._log(f"ERRO: {exc}")
            QMessageBox.critical(self, "Erro", str(exc))
        finally:
            self.progress.setVisible(False)
            self.btn_clip.setEnabled(True)

    def _generate_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Relatorio PDF", f"Relatorio_MapBiomas_{self.last_year}.pdf", "PDF (*.pdf)")
        if not path: return

        try:
            self._log("Gerando relatorio PDF via QGIS Layout Engine...")
            summary = self.ee_handler.get_area_summary(self.last_vector_path)
            palette = self.ee_handler.MAPBIOMAS_PALETTE
            
            if generate_qgis_pdf_report(path, self.last_layer_name, self.last_year, summary, palette, self.canvas, self._log):
                QMessageBox.information(self, "Sucesso", f"Relatorio gerado em:\n{path}")
                output_dir = os.path.dirname(path)
                QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))
            else:
                QMessageBox.critical(self, "Erro", "Falha ao gerar o PDF via QGIS. Verifique o log.")
        except Exception as e:
            self._log(f"Erro no PDF: {e}")
            QMessageBox.critical(self, "Erro", str(e))

    def _update_progress(self, value):
        self.progress.setValue(value)
        QCoreApplication.processEvents()

    def _get_geometries_4326(self, layer):
        geoms = []
        dest_crs = QgsCoordinateReferenceSystem('EPSG:4326')
        src_crs = layer.crs()
        transform = QgsCoordinateTransform(src_crs, dest_crs, QgsProject.instance())
        for feat in layer.getFeatures():
            geom = feat.geometry()
            if src_crs != dest_crs: geom.transform(transform)
            geoms.append(geom)
        return geoms
