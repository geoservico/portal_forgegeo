# -*- coding: utf-8 -*-

def classFactory(iface):
    from .portal_plugin import PortalForgegeoPlugin
    return PortalForgegeoPlugin(iface)
