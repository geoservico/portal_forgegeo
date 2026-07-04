# -*- coding: utf-8 -*-
"""
GeoServico-CLIPPER - Plugin Principal
Acesso direto ao MapBiomas via Google Cloud Storage (sem autenticacao)
"""

import os

from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis

try:
    from .dialog import GeoServicioClipperDialog
    from .earth_engine_handler import EarthEngineHandler
    from .utils import setup_logger
except ImportError as e:
    print(f"[GeoServico-CLIPPER] Erro ao importar modulos: {e}")
    raise


class GeoServicio_Clipper:
    """Classe principal do plugin GeoServico-CLIPPER"""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = u'&GeoServico-CLIPPER'
        self.toolbar = None
        self.dialog = None

        self.logger = setup_logger('GeoServico-CLIPPER')
        self.ee_handler = EarthEngineHandler()
        self.logger.info("Plugin inicializado (acesso publico MapBiomas)")

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(
            icon,
            u'GeoServico-CLIPPER - Recortar MapBiomas',
            self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)
        self.action.setStatusTip(
            u'Recortar imagens MapBiomas usando mascara vetorial')

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.actions.append(self.action)
        self.logger.info("Interface inicializada")

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        if self.toolbar:
            del self.toolbar
        self.logger.info("Plugin descarregado")

    def run(self):
        if self.dialog is None:
            self.dialog = GeoServicioClipperDialog(
                self.iface, self.ee_handler, self.logger)
        self.dialog.show()
        self.dialog.exec_()
