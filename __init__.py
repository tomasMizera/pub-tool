#-----------------------------------------------------------
# Copyright (C) 2015 Martin Dobias
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.gui import QgsMapToolEmitPoint
from qgis.core import QgsSpatialIndex

def classFactory(iface):
    return PubTool(iface)


class PubTool:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction('Pub!', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

        self.initialize()

    def initialize(self):
        # build index
        self.index = QgsSpatialIndex(self.iface.activeLayer().getFeatures())

        self.pubTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pubTool.canvasClicked.connect(self.handle_click)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action, self.pubTool, self.index

    def run(self):
        self.iface.mapCanvas().setMapTool(self.pubTool)

    def handle_click(self, point):
        nearest = self.index.nearestNeighbor(point,1)
        msg = f'You are at x: {point.x()} y: {point.y()}\
            \nNearest point to you: {nearest}'

        QMessageBox.information(None, 'Pub Tool', msg)
