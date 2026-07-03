# -*- coding: utf-8 -*-
"""
Gerador de Relatorios PDF Profissional para o GeoServico-CLIPPER
Utiliza o QGIS Layout Engine para gerar documentos em orientacao Retrato (A4),
sem molduras e com design harmonizado e profissional.
"""

import os
import traceback
from datetime import datetime

from qgis.PyQt.QtGui import QFont, QColor
from qgis.core import (
    QgsProject, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemHtml, QgsLayoutExporter, QgsLayoutSize, QgsUnitTypes, 
    QgsLayoutPoint, QgsLayoutItemPage, QgsLayoutFrame
)

def generate_qgis_pdf_report(output_pdf, layer_name, year, area_summary, palette, canvas, logger=None):
    """
    Gera o relatorio PDF harmonizado e profissional usando o motor de impressao do QGIS
    """
    def log(msg):
        if logger: logger(msg)
        print(f"[QGISReport] {msg}")

    try:
        log("Iniciando geracao de relatorio harmonizado (Retrato)...")
        project = QgsProject.instance()
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(f"Relatorio_Profissional_{year}_{int(datetime.now().timestamp())}")

        # 1. Configurar Pagina (A4 Retrato)
        page = layout.pageCollection().pages()[0]
        page.setPageSize('A4', QgsLayoutItemPage.Portrait)

        # 2. Cabecalho Simplificado (v7.0.9)
        # Titulo Unico: Analise Temporal - Ano [ANO]
        title = QgsLayoutItemLabel(layout)
        title.setText(f"Análise Temporal - Ano {year}")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setFontColor(QColor("#1a1a1a"))
        title.adjustSizeToText()
        layout.addLayoutItem(title)
        title.attemptMove(QgsLayoutPoint(15, 15, QgsUnitTypes.LayoutMillimeters))

        # 3. Mapa Centralizado e Sem Moldura
        map_item = QgsLayoutItemMap(layout)
        # Tamanho proporcional para A4 Retrato (Largura: 180mm, Altura: 130mm)
        map_item.setRect(0, 0, 180, 130)
        map_item.setExtent(canvas.extent())
        map_item.setBackgroundColor(QColor(255, 255, 255))
        layout.addLayoutItem(map_item)
        map_item.attemptMove(QgsLayoutPoint(15, 30, QgsUnitTypes.LayoutMillimeters))
        map_item.attemptResize(QgsLayoutSize(180, 140, QgsUnitTypes.LayoutMillimeters))
        # Remover moldura conforme solicitado
        map_item.setFrameEnabled(False)

        # 4. Painel de Informacoes do Projeto (Abaixo do Mapa)
        info_box = QgsLayoutItemLabel(layout)
        txt_info = (f"IMÓVEL/MÁSCARA: {layer_name}\n"
                    f"DATA DE GERAÇÃO: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                    f"FONTE DE DADOS: MAPBIOMAS COLLECTION 10 (30m)")
        info_box.setText(txt_info)
        info_box.setFont(QFont("Segoe UI", 9))
        info_box.setFontColor(QColor("#666666"))
        info_box.adjustSizeToText()
        layout.addLayoutItem(info_box)
        info_box.attemptMove(QgsLayoutPoint(15, 175, QgsUnitTypes.LayoutMillimeters))

        # 5. Tabela de Areas Consolidada (HTML Estilizado)
        html_item = QgsLayoutItemHtml(layout)
        
        rows_html = ""
        total_area = sum(area_summary.values())
        
        # Mapear nome da classe para cor RGB
        name_to_color = {}
        for code, data in palette.items():
            name_to_color[data['name']] = data['color']
        
        # Ordenar classes por area decrescente
        sorted_classes = sorted(area_summary.items(), key=lambda x: x[1], reverse=True)
        
        for i, (name, area) in enumerate(sorted_classes):
            rgb = name_to_color.get(name, (200, 200, 200))
            hex_color = '#%02x%02x%02x' % rgb
            bg_row = "#f9f9f9" if i % 2 == 0 else "#ffffff"
            rows_html += f"""
            <tr style='background-color:{bg_row};'>
                <td style='width:12px; height:12px; background-color:{hex_color}; border-radius:2px;'></td>
                <td style='padding:6px; border-bottom:1px solid #eee;'>{name}</td>
                <td style='padding:6px; border-bottom:1px solid #eee; text-align:right; font-weight:bold;'>{area:,.2f} ha</td>
            </tr>
            """
        
        full_html = f"""
        <html>
        <head>
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ border-bottom: 2px solid #1f8d49; color: #1f8d49; padding: 8px; text-align: left; font-size: 10pt; text-transform: uppercase; letter-spacing: 1px; }}
            td {{ font-size: 9.5pt; vertical-align: middle; }}
            .total-row {{ background-color: #1f8d49 !important; color: white !important; font-weight: bold; }}
        </style>
        </head>
        <body>
        <table>
            <thead>
                <tr>
                    <th colspan='2'>Legenda / Classe MapBiomas</th>
                    <th style='text-align:right;'>Área Calculada</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
                <tr class='total-row'>
                    <td colspan='2' style='padding:10px; border-radius: 0 0 0 4px;'>ÁREA TOTAL DO RECORTE</td>
                    <td style='padding:10px; text-align:right; border-radius: 0 0 4px 0;'>{total_area:,.2f} ha</td>
                </tr>
            </tbody>
        </table>
        </body>
        </html>
        """
        
        html_item.setContentMode(QgsLayoutItemHtml.ManualHtml)
        html_item.setHtml(full_html)
        
        # Frame para a tabela (Abaixo das informacoes)
        frame = QgsLayoutFrame(layout, html_item)
        frame.attemptMove(QgsLayoutPoint(15, 190, QgsUnitTypes.LayoutMillimeters))
        frame.attemptResize(QgsLayoutSize(180, 90, QgsUnitTypes.LayoutMillimeters))
        frame.setFrameEnabled(False)
        
        html_item.addFrame(frame)
        layout.addMultiFrame(html_item)
        
        # Forcar renderizacao do HTML
        html_item.loadHtml()

        # 6. Rodape de Pagina
        footer = QgsLayoutItemLabel(layout)
        footer.setText("Gerado automaticamente pelo GeoServiço-CLIPPER | Plugin QGIS v7.0.9")
        footer.setFont(QFont("Segoe UI", 7, QFont.StyleItalic))
        footer.setFontColor(QColor("#999999"))
        footer.adjustSizeToText()
        layout.addLayoutItem(footer)
        footer.attemptMove(QgsLayoutPoint(15, 285, QgsUnitTypes.LayoutMillimeters))

        # 7. Exportar para PDF
        exporter = QgsLayoutExporter(layout)
        settings = QgsLayoutExporter.PdfExportSettings()
        result = exporter.exportToPdf(output_pdf, settings)
        
        if result == QgsLayoutExporter.Success:
            log("✓ Relatório profissional (Retrato) gerado com sucesso.")
            return True
        else:
            log(f"Falha na exportação. Código: {result}")
            return False

    except Exception as e:
        log(f"Erro no motor de relatórios: {str(e)}")
        log(traceback.format_exc())
        return False
