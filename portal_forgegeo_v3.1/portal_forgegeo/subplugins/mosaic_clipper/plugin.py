import os
from qgis.core import QgsApplication
from qgis.gui import QgsMapLayerComboBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

class MosaicClipper:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.name = 'Mosaic Clipper'
        self.description = 'Plugin para recorte e exportação de imagens Landsat (2000-2025) em falsa cor via Google Earth Engine, com autenticação obrigatória.'
        self.icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = None
        self.dlg = None

    def initGui(self):
        self.action = QAction(QIcon(self.icon_path), self.name, self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(self.name, self.action)

    def unload(self):
        self.iface.removePluginMenu(self.name, self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        from .dialog import MosaicClipperDialog
        self.dlg = MosaicClipperDialog()
        self.dlg.show()
