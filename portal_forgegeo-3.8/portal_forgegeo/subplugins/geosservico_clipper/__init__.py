# -*- coding: utf-8 -*-
"""
GeoServico-CLIPPER Plugin for QGIS 3.40+
Recortar imagens MapBiomas usando mascara vetorial.
Acesso direto via Google Cloud Storage (sem autenticacao).

Author: Tecno. Geoproc. Fabricio Marcal
"""


def classFactory(iface):
    from .plugin import GeoServicio_Clipper
    return GeoServicio_Clipper(iface)
