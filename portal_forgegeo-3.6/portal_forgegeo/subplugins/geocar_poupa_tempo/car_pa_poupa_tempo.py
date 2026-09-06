import os
from qgis.core import (QgsProject, QgsVectorLayer, QgsCoordinateReferenceSystem, 
                       QgsCoordinateTransform, QgsLayerTreeGroup, QgsField)
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from .car_dialog import CarDialog

class CarPaPoupaTempo:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = 'GeoCAR Poupa Tempo'

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon_path), 'Abrir GeoCAR Poupa Tempo', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)
        self.actions.append(self.action)

    def unload(self):
        for action in self.actions:
            self.iface.removeToolBarIcon(action)
            self.iface.removePluginMenu(self.menu, action)

    def run(self):
        self.dialog = CarDialog()
        self.dialog.create_layers_btn.clicked.connect(self.create_car_layers)
        self.dialog.export_btn.clicked.connect(self.export_layers)
        self.dialog.show()

    def create_car_layers(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()

        # Define o CRS SIRGAS 2000 Geográficas (EPSG:4674)
        target_crs = QgsCoordinateReferenceSystem('EPSG:4674')

        self.dialog.log_message("Iniciando criação de grupos e camadas...")
        self.dialog.progress_bar.setVisible(True)
        progress = 0

        # Estrutura de grupos e camadas
        layer_structure = {}
        
        if self.dialog.imovel_check.isChecked():
            layer_structure['Imóvel'] = {
                'Imóvel': 'MultiPolygon',
                'Sede': 'Point'
            }
            
        if self.dialog.cobertura_check.isChecked():
            layer_structure['Cobertura do Solo'] = {
                'Área Consolidada': 'MultiPolygon',
                'Remanescente de Vegetação Nativa': 'MultiPolygon',
                'Área de Pousio': 'MultiPolygon',
                'Área de Regeneração': 'MultiPolygon'
            }
            
        if self.dialog.servidao_check.isChecked():
            layer_structure['Servidão Administrativa'] = {
                'Infraestrutura Pública': ['MultiPolygon', 'LineString'],
                'Utilidade Pública': ['MultiPolygon', 'LineString'],
                'Reservatório para Abastecimento ou Geração de Energia': 'MultiPolygon',
                'Servidão Minerária': 'MultiPolygon'
            }
            
        if self.dialog.app_check.isChecked():
            layer_structure['APP/Uso Restrito'] = {
                'Uso Restrito': {
                    'Área de Uso Restrito para declividade de 25 a 45 graus': 'MultiPolygon',
                    'Área de Uso Restrito para regiões pantaneiras': 'MultiPolygon'
                },
                'Área de Preservação Permanente': {
                    'Curso d\'água natural com até 10metros': ['MultiPolygon', 'LineString'],
                    'Curso d\'água natural de 10 a 50 metros': 'MultiPolygon',
                    'Curso d\'água natural de 50 a 200 metros': 'MultiPolygon',
                    'Curso d\'água natural de 200 a 600 metros': 'MultiPolygon',
                    'Curso d\'água natural acima de 600 metros': 'MultiPolygon',
                    'Lago ou lagoa natural': 'MultiPolygon',
                    'Nascente ou olho d\'agua perene': 'Point',
                    'Reservatório artificial decorrente de barramento ou represamento de cursos d\'água naturais': 'MultiPolygon',
                    'Reservatório de geração de energia elétrica construído até 24/08/2001': 'MultiPolygon',
                    'Banhado': 'MultiPolygon',
                    'Manguezal': 'MultiPolygon',
                    'Restinga': 'MultiPolygon',
                    'Vereda': 'MultiPolygon',
                    'Área com altitude superior a 1.800 metros': 'MultiPolygon',
                    'Área de declividade maior que 45 graus': 'MultiPolygon',
                    'Borda de chapada': 'MultiPolygon',
                    'Área de topo de morro': 'MultiPolygon'
                }
            }
            
        if self.dialog.reserva_check.isChecked():
            layer_structure['Reserva Legal'] = {
                'Reserva Legal Proposta': 'MultiPolygon',
                'Reserva Legal Averbada': 'MultiPolygon',
                'Reserva Legal Aprovada e não Averbada': 'MultiPolygon',
                'Reserva legal vinculada à compensação de outro imóvel': 'MultiPolygon'
            }

        total_items = self.count_total_items(layer_structure)
        current_item = 0

        def create_group_and_layers(parent_group, structure):
            nonlocal current_item
            for name, content in structure.items():
                if isinstance(content, dict):
                    # É um subgrupo
                    new_group = parent_group.addGroup(name)
                    self.dialog.log_message(f"Criando grupo: {name}")
                    create_group_and_layers(new_group, content)
                else:
                    # É uma camada
                    geom_types = content if isinstance(content, list) else [content]
                    for geom_type in geom_types:
                        layer_name = f'{name} ({geom_type})' if len(geom_types) > 1 else name
                        uri = f'{geom_type}?crs=epsg:4674'
                        layer = QgsVectorLayer(uri, layer_name, 'memory')
                        if not layer.isValid():
                            self.dialog.log_message(f'Erro ao criar camada: {layer_name}')
                            continue
                        
                        # Adiciona campos básicos
                        layer.dataProvider().addAttributes([
                            QgsField('id', QVariant.Int),
                            QgsField('nome', QVariant.String, len=255),
                            QgsField('descricao', QVariant.String, len=500),
                            QgsField('data_criacao', QVariant.Date)
                        ])
                        layer.updateFields()
                        
                        project.addMapLayer(layer, False)
                        parent_group.addLayer(layer)
                        
                        current_item += 1
                        progress = int((current_item / total_items) * 100)
                        self.dialog.progress_bar.setValue(progress)
                        self.dialog.log_message(f"Camada criada: {layer_name}")

        create_group_and_layers(root, layer_structure)
        
        self.dialog.progress_bar.setValue(100)
        self.dialog.log_message("Todas as camadas e grupos foram criados com sucesso!")
        self.dialog.export_btn.setEnabled(True)
        
        if self.dialog.auto_export_check.isChecked():
            self.export_layers()

    def count_total_items(self, structure):
        count = 0
        for name, content in structure.items():
            if isinstance(content, dict):
                count += self.count_total_items(content)
            else:
                geom_types = content if isinstance(content, list) else [content]
                count += len(geom_types)
        return count

    def export_layers(self):
        import zipfile
        import tempfile
        from qgis.core import QgsVectorFileWriter, QgsCoordinateReferenceSystem
        
        self.dialog.log_message("Iniciando exportação das camadas...")
        self.dialog.progress_bar.setVisible(True)
        self.dialog.progress_bar.setValue(0)
        
        # Obter nome do cliente e formatar nome da pasta
        client_name = self.dialog.client_name_input.text().strip()
        folder_name = "CAR FINALIZADO"
        if client_name:
            # Limpar nome do cliente para evitar caracteres inválidos em nomes de pasta
            safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            folder_name = f"CAR FINALIZADO {safe_client_name}"
            
        # Criar pasta no desktop
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        car_folder = os.path.join(desktop_path, folder_name)
        
        if not os.path.exists(car_folder):
            os.makedirs(car_folder)
            self.dialog.log_message(f"Pasta criada: {car_folder}")
        
        project = QgsProject.instance()
        layers = project.mapLayers().values()
        
        # Filtrar apenas camadas vetoriais
        vector_layers = [layer for layer in layers if isinstance(layer, QgsVectorLayer)]
        
        if not vector_layers:
            self.dialog.log_message("Nenhuma camada vetorial encontrada para exportar.")
            return
        
        total_layers = len(vector_layers)
        current_layer = 0
        
        # CRS SIRGAS 2000 Geográficas
        target_crs = QgsCoordinateReferenceSystem('EPSG:4674')
        
        for layer in vector_layers:
            try:
                current_layer += 1
                progress = int((current_layer / total_layers) * 100)
                self.dialog.progress_bar.setValue(progress)
                
                layer_name = layer.name()
                # Limpar nome do arquivo (remover caracteres especiais)
                safe_name = "".join(c for c in layer_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_')
                
                self.dialog.log_message(f"Exportando camada: {layer_name}")
                
                # Criar pasta temporária para os arquivos shapefile
                with tempfile.TemporaryDirectory() as temp_dir:
                    shapefile_path = os.path.join(temp_dir, f"{safe_name}.shp")
                    
                    # Configurar opções de exportação
                    options = QgsVectorFileWriter.SaveVectorOptions()
                    options.driverName = "ESRI Shapefile"
                    options.fileEncoding = "UTF-8"
                    
                    # Transformar para SIRGAS 2000 se necessário
                    if layer.crs() != target_crs:
                        options.ct = QgsCoordinateTransform(layer.crs(), target_crs, project)
                    
                    # Exportar para shapefile
                    error = QgsVectorFileWriter.writeAsVectorFormatV3(
                        layer,
                        shapefile_path,
                        project.transformContext(),
                        options
                    )
                    
                    if error[0] == QgsVectorFileWriter.WriterError.NoError:
                        # Criar arquivo ZIP
                        zip_path = os.path.join(car_folder, f"{safe_name}.zip")
                        
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                            # Adicionar todos os arquivos do shapefile ao ZIP
                            for file in os.listdir(temp_dir):
                                if file.startswith(safe_name):
                                    file_path = os.path.join(temp_dir, file)
                                    zipf.write(file_path, file)
                        
                        self.dialog.log_message(f"Camada exportada: {safe_name}.zip")
                    else:
                        self.dialog.log_message(f"Erro ao exportar {layer_name}: {error[1]}")
                        
            except Exception as e:
                self.dialog.log_message(f"Erro ao processar camada {layer_name}: {str(e)}")
        
        self.dialog.progress_bar.setValue(100)
        self.dialog.log_message(f"Exportação concluída! Arquivos salvos em: {car_folder}")
        
        # Abrir a pasta no explorador usando a API Qt, sem executar comandos
        # externos ou interpretar o caminho como shell.
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(car_folder))
        except (OSError, RuntimeError) as error:
            self.dialog.log_message(f"Não foi possível abrir a pasta exportada: {error}")



