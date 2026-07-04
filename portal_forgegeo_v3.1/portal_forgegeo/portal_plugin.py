# -*- coding: utf-8 -*-
import os
import requests
from qgis.PyQt.QtWidgets import (QAction, QMessageBox, QDialog, QVBoxLayout, 
                                 QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                                 QProgressBar, QFrame, QGridLayout, QScrollArea,
                                 QGroupBox, QSizePolicy)
from qgis.PyQt.QtGui import QIcon, QPixmap, QFont
from qgis.PyQt.QtCore import Qt, QSettings, QSize
from qgis.core import Qgis, QgsMessageLog

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - Portal - FORGEGEO")
        self.setFixedSize(400, 350)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "icon.png")
        pixmap = QPixmap(logo_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Título
        title_label = QLabel("Portal - FORGEGEO")
        title_font = QFont("Arial", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        layout.addSpacing(10)
        
        # Campos de Login
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuário")
        self.user_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        layout.addWidget(self.user_input)
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Senha")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        layout.addWidget(self.pass_input)
        
        layout.addSpacing(10)
        
        # Botão de Login
        self.login_btn = QPushButton("Entrar")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
        """)
        self.login_btn.clicked.connect(self.accept)
        layout.addWidget(self.login_btn)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)

class PortalDialog(QDialog):
    def __init__(self, plugins_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Painel Portal - FORGEGEO")
        self.setMinimumSize(800, 600)
        self.plugins_info = plugins_info
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;")
        header_layout = QHBoxLayout(header)
        
        title_label = QLabel("Painel de Ferramentas")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.logout_btn = QPushButton("Sair")
        self.logout_btn.setStyleSheet("padding: 5px 15px; background-color: #dc3545; color: white; border-radius: 3px;")
        header_layout.addWidget(self.logout_btn)
        
        main_layout.addWidget(header)
        
        # Scroll Area para os Plugins
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QFrame()
        grid = QGridLayout(container)
        grid.setSpacing(20)
        grid.setContentsMargins(20, 20, 20, 20)
        
        cols = 2
        for i, (p_id, info) in enumerate(self.plugins_info.items()):
            row = i // cols
            col = i % cols
            
            card = QGroupBox(info['name'])
            card.setFixedSize(360, 220)
            card.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #e9ecef;
                    border-radius: 10px;
                    margin-top: 20px;
                    background-color: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }
            """)
            
            card_layout = QVBoxLayout(card)
            
            # Ícone
            icon_label = QLabel()
            pixmap = QIcon(info['icon']).pixmap(QSize(80, 80))
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(icon_label)
            
            # Descrição Curta
            desc = QLabel(info.get('desc', 'Plugin Forgegeo'))
            desc.setWordWrap(True)
            desc.setAlignment(Qt.AlignCenter)
            desc.setStyleSheet("font-size: 12px; color: #666;")
            card_layout.addWidget(desc)
            
            # Botão Abrir
            btn = QPushButton("Abrir")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #198754;
                    color: white;
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #157347;
                }
            """)
            btn.clicked.connect(info['callback'])
            card_layout.addWidget(btn)
            
            grid.addWidget(card, row, col)
            
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

class PortalForgegeoPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.settings = QSettings("Forgegeo", "PortalPlugin")
        self.username = None
        self.password = None
        self.authenticated = False
        self.subplugins = {}
        self.portal_dialog = None
        
    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "icon.png")
        self.action = QAction(QIcon(icon_path), "Portal - FORGEGEO", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("Portal - FORGEGEO", self.action)
        
        self.setup_subplugins()
        
    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("Portal - FORGEGEO", self.action)

    def check_dependencies(self):
        """Verifica e instala dependências necessárias para os subplugins"""
        from .dependency_manager import install_dependencies
        requirements = [
            ('earthengine-api', 'ee'),
            ('google-api-python-client', 'googleapiclient'),
            ('requests', 'requests'),
            ('numpy', 'numpy'),
            ('beautifulsoup4', 'bs4'),
            ('psycopg2-binary', 'psycopg2')
        ]
        return install_dependencies(requirements)

    def setup_subplugins(self):
        """Inicializa os subplugins disponíveis"""
        # Não instalamos dependências aqui no initGui para não travar o carregamento do QGIS
        # As dependências serão verificadas ao abrir o portal ou o subplugin
        
        configs = [
            {
                'id': 'mosaic',
                'name': 'Mosaic Clipper',
                'module': '.subplugins.mosaic_clipper.plugin',
                'class': 'MosaicClipper',
                'icon': 'subplugins/mosaic_clipper/icon.png',
                'desc': 'Geração de mosaicos e recortes GEE'
            },
            {
                'id': 'geonexus',
                'name': 'GeoNexus',
                'module': '.subplugins.geonexus.geoservico_insumos_plugin',
                'class': 'GeoservicoInsumosPlugin',
                'icon': 'subplugins/geonexus/icon.png',
                'desc': 'Análise técnica do CAR e processamento de camadas'
            },
            {
                'id': 'poupa_tempo',
                'name': 'GeoCAR Poupa Tempo',
                'module': '.subplugins.geocar_poupa_tempo.car_pa_poupa_tempo',
                'class': 'CarPaPoupaTempo',
                'icon': 'subplugins/geocar_poupa_tempo/icon.png',
                'desc': 'Automação da criação de grupos e camadas para o CAR'
            },
            {
                'id': 'geosservico_clipper',
                'name': 'GeoServico Clipper',
                'module': '.subplugins.geosservico_clipper.plugin',
                'class': 'GeoServicio_Clipper',
                'icon': 'subplugins/geosservico_clipper/icon.png',
                'desc': 'Recorte de imagens MapBiomas e relatórios PDF'
            }
        ]
        
        import importlib
        for cfg in configs:
            # Criamos o callback de lançamento mesmo que o import falhe inicialmente
            # O import real acontecerá apenas no momento do clique se necessário
            self.subplugins[cfg['id']] = {
                'id': cfg['id'],
                'name': cfg['name'],
                'module': cfg['module'],
                'class': cfg['class'],
                'icon': os.path.join(self.plugin_dir, cfg['icon']),
                'desc': cfg['desc'],
                'instance': None, # Será instanciado sob demanda
                'callback': (lambda c=cfg: lambda: self.launch_subplugin_by_cfg(c))()
            }

    def launch_subplugin_by_cfg(self, cfg):
        """Instancia e lança o subplugin sob demanda"""
        try:
            # Se já instanciado, usa a instância existente
            if self.subplugins[cfg['id']]['instance'] is None:
                import importlib
                mod = importlib.import_module(cfg['module'], package='portal_forgegeo')
                cls = getattr(mod, cfg['class'])
                self.subplugins[cfg['id']]['instance'] = cls(self.iface)
            
            instance = self.subplugins[cfg['id']]['instance']
            
            # Passa credenciais se o plugin suportar
            if hasattr(instance, 'usuario') or hasattr(instance, 'username'):
                if hasattr(instance, 'usuario'): instance.usuario = self.username
                if hasattr(instance, 'username'): instance.username = self.username
                if hasattr(instance, 'senha'): instance.senha = self.password
                if hasattr(instance, 'password'): instance.password = self.password
                instance.is_authenticated = True
                
            if hasattr(instance, 'run'):
                instance.run()
            else:
                QMessageBox.warning(self.iface.mainWindow(), "Aviso", f"O subplugin {cfg['name']} não possui um método de execução padrão.")
                
        except Exception as e:
            QgsMessageLog.logMessage(f"Erro ao carregar subplugin {cfg['name']}: {str(e)}", "PortalForgegeo", Qgis.Critical)
            QMessageBox.critical(self.iface.mainWindow(), "Erro de Carregamento", f"Não foi possível carregar o subplugin {cfg['name']}.\nErro: {str(e)}")

    def launch_subplugin(self, instance):
        """Lança o plugin selecionado (legado)"""
        if instance and hasattr(instance, 'run'):
            instance.run()

    def authenticate(self, user, password):
        """Valida credenciais no GeoServer"""
        url = "http://srv1185637.hstgr.cloud:8082/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities"
        try:
            r = requests.get(url, auth=(user, password), timeout=10)
            return r.status_code == 200
        except:
            return False

    def run(self):
        # Verifica dependências antes de qualquer coisa
        if not self.check_dependencies():
            return

        if not self.authenticated:
            self.login_dlg = LoginDialog(self.iface.mainWindow())
            self.login_dlg.setModal(False)
            self.login_dlg.accepted.connect(self.on_login_accepted)
            self.login_dlg.show()
        else:
            self.show_portal()

    def on_login_accepted(self):
        user = self.login_dlg.user_input.text()
        pw = self.login_dlg.pass_input.text()
        
        if self.authenticate(user, pw):
            self.username = user
            self.password = pw
            self.authenticated = True
            self.show_portal()
        else:
            QMessageBox.critical(self.iface.mainWindow(), "Erro", "Usuário ou senha inválidos no GeoServer.")

    def show_portal(self):
        if self.portal_dialog is None:
            self.portal_dialog = PortalDialog(self.subplugins, self.iface.mainWindow())
            self.portal_dialog.setModal(False)
            self.portal_dialog.logout_btn.clicked.connect(self.logout)
            
        self.portal_dialog.show()
        self.portal_dialog.raise_()
        self.portal_dialog.activateWindow()

    def logout(self):
        self.authenticated = False
        self.username = None
        self.password = None
        if self.portal_dialog:
            self.portal_dialog.close()
        QMessageBox.information(self.iface.mainWindow(), "Logout", "Você saiu do portal.")
