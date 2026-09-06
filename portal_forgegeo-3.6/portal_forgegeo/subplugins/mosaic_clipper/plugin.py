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
        self.description = 'Plugin para seleção anual, melhoria visual e recorte de imagens Landsat 5, 7, 8 e 9, SPOT 2, 4 e 5 e Sentinel-2 via Google Earth Engine.'
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
