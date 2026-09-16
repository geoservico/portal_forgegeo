import os
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QProgressBar, QTextEdit, QGroupBox, 
                             QCheckBox, QFrame, QScrollArea, QWidget, QLineEdit)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QFont, QPixmap, QPalette, QColor

class CarDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GeoCAR Poupa Tempo")
        self.setFixedSize(600, 700)
        self.setStyleSheet(self.get_modern_style())
        self.setup_ui()

    def get_modern_style(self):
        return """
        QDialog {
            background-color: #f8f9fa;
            border-radius: 10px;
        }
        
        QLabel {
            color: #2c3e50;
            font-weight: 500;
        }
        
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin: 10px 0;
        }
        
        .subtitle {
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 20px;
        }
        
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 14px;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #21618c;
        }
        
        QPushButton:disabled {
            background-color: #bdc3c7;
        }
        
        .primary-button {
            background-color: #27ae60;
        }
        
        .primary-button:hover {
            background-color: #229954;
        }
        
        .secondary-button {
            background-color: #e74c3c;
        }
        
        .secondary-button:hover {
            background-color: #c0392b;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #bdc3c7;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #2c3e50;
        }
        
        QCheckBox {
            spacing: 8px;
            color: #2c3e50;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        
        QCheckBox::indicator:unchecked {
            border: 2px solid #bdc3c7;
            border-radius: 3px;
            background-color: white;
        }
        
        QCheckBox::indicator:checked {
            border: 2px solid #3498db;
            border-radius: 3px;
            background-color: #3498db;
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
        }
        
        QProgressBar {
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            text-align: center;
            background-color: #ecf0f1;
        }
        
        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 3px;
        }
        
        QTextEdit, QLineEdit {
            border: 2px solid #bdc3c7;
            border-radius: 6px;
            padding: 8px;
            background-color: white;
            color: #2c3e50;
        }
        
        QLineEdit:focus {
            border: 2px solid #3498db;
        }
        
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QFrame {
            background-color: transparent;
        }
        """

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header_layout = QVBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "geoservicologo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)
        
        title_label = QLabel("GeoCAR Poupa Tempo")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("Desenvolvido por Geoserviço - Geotecnologias & Meio Ambiente")
        subtitle_label.setProperty("class", "subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addLayout(header_layout)

        # Scroll area for options
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Grupos de camadas
        self.create_layer_groups(scroll_layout)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(350)
        
        main_layout.addWidget(scroll_area)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Log area
        log_group = QGroupBox("Log de Operações")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.create_layers_btn = QPushButton("Criar Camadas")
        self.create_layers_btn.setProperty("class", "primary-button")
        
        self.export_btn = QPushButton("Exportar Camadas")
        self.export_btn.setEnabled(False)
        
        self.close_btn = QPushButton("Fechar")
        self.close_btn.setProperty("class", "secondary-button")
        
        button_layout.addWidget(self.create_layers_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)

        # Connect signals
        self.create_layers_btn.clicked.connect(self.create_layers)
        self.export_btn.clicked.connect(self.export_layers)
        self.close_btn.clicked.connect(self.close)

    def create_layer_groups(self, layout):
        # Grupo Imóvel
        imovel_group = QGroupBox("Imóvel")
        imovel_layout = QVBoxLayout()
        self.imovel_check = QCheckBox("Criar grupo Imóvel (Imóvel + Sede)")
        self.imovel_check.setChecked(True)
        imovel_layout.addWidget(self.imovel_check)
        imovel_group.setLayout(imovel_layout)
        layout.addWidget(imovel_group)

        # Grupo Cobertura do Solo
        cobertura_group = QGroupBox("Cobertura do Solo")
        cobertura_layout = QVBoxLayout()
        self.cobertura_check = QCheckBox("Criar grupo Cobertura do Solo")
        self.cobertura_check.setChecked(True)
        cobertura_layout.addWidget(self.cobertura_check)
        cobertura_group.setLayout(cobertura_layout)
        layout.addWidget(cobertura_group)

        # Grupo Servidão Administrativa
        servidao_group = QGroupBox("Servidão Administrativa")
        servidao_layout = QVBoxLayout()
        self.servidao_check = QCheckBox("Criar grupo Servidão Administrativa")
        self.servidao_check.setChecked(True)
        servidao_layout.addWidget(self.servidao_check)
        servidao_group.setLayout(servidao_layout)
        layout.addWidget(servidao_group)

        # Grupo APP/Uso Restrito
        app_group = QGroupBox("APP/Uso Restrito")
        app_layout = QVBoxLayout()
        self.app_check = QCheckBox("Criar grupo APP/Uso Restrito")
        self.app_check.setChecked(True)
        app_layout.addWidget(self.app_check)
        app_group.setLayout(app_layout)
        layout.addWidget(app_group)

        # Grupo Reserva Legal
        reserva_group = QGroupBox("Reserva Legal")
        reserva_layout = QVBoxLayout()
        self.reserva_check = QCheckBox("Criar grupo Reserva Legal")
        self.reserva_check.setChecked(True)
        reserva_layout.addWidget(self.reserva_check)
        reserva_group.setLayout(reserva_layout)
        layout.addWidget(reserva_group)

        # Opção de exportação
        export_group = QGroupBox("Opções de Exportação")
        export_layout = QVBoxLayout()
        
        # Campo para nome do cliente
        client_layout = QHBoxLayout()
        client_label = QLabel("Nome do Cliente:")
        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("Digite o nome do cliente...")
        client_layout.addWidget(client_label)
        client_layout.addWidget(self.client_name_input)
        export_layout.addLayout(client_layout)
        
        self.auto_export_check = QCheckBox("Exportar automaticamente após criação")
        self.auto_export_check.setChecked(False)
        export_layout.addWidget(self.auto_export_check)
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)

    def create_layers(self):
        self.log_text.append("Iniciando criação de camadas...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Aqui será chamada a função de criação de camadas
        # Por enquanto, simulamos o progresso
        for i in range(101):
            self.progress_bar.setValue(i)
            
        self.log_text.append("Camadas criadas com sucesso!")
        self.export_btn.setEnabled(True)
        
        if self.auto_export_check.isChecked():
            self.export_layers()

    def export_layers(self):
        self.log_text.append("Iniciando exportação das camadas...")
        self.progress_bar.setValue(0)
        
        # Aqui será implementada a lógica de exportação
        for i in range(101):
            self.progress_bar.setValue(i)
            
        self.log_text.append("Exportação concluída! Arquivos salvos em 'CAR FINALIZADO' no desktop.")

    def log_message(self, message):
        self.log_text.append(message)

