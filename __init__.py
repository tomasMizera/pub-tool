# -----------------------------------------------------------
# Copyright (C) 2015 Martin Dobias
# -----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# ---------------------------------------------------------------------

from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.gui import QgsMapToolEmitPoint
from qgis.core import QgsSpatialIndex, QgsFeatureRequest, \
    QgsCoordinateTransform, QgsCoordinateReferenceSystem, \
    QgsProject, Qgis, QgsPoint, QgsPointXY, QgsDistanceArea


def classFactory(iface):
    return PubTool(iface)


class PubTool:
    def __init__(self, iface):
        self.iface = iface
        self.index_built = False

    def initGui(self):
        self.action = QAction('Pub!', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

        # build map tool
        self.mapTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.mapTool.canvasClicked.connect(self.handle_click)

        #build projection transformer
        self.pj_transformer = QgsCoordinateTransform(\
            QgsCoordinateReferenceSystem("EPSG:4326"),\
            QgsCoordinateReferenceSystem("EPSG:5514"),\
            QgsProject.instance())
        self.allowed_projections = ["EPSG:4326", "EPSG:5514"]

        #Calculate distance
        self.distance_calculator = QgsDistanceArea()
        self.distance_calculator.setSourceCrs(QgsCoordinateReferenceSystem("EPSG:5514"))

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action, self.index, self.mapTool
        del self.pj_transformer, self.allowed_projections, self.index_built

    def build_index(self):
        self.index = QgsSpatialIndex(self.iface.activeLayer().getFeatures())
        self.index_built = True

    def run(self):
        if (not self.index_built):
            self.build_index()
        
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def get_nearest_point_name(self, point):

        # Check for projection
        c_proj = self.iface.mapCanvas().mapSettings().destinationCrs().authid()
        if c_proj not in self.allowed_projections:
            raise Exception (f'Your canvas projection {c_proj} is not allowed with plugin pub-tools;\
                 allowed projections: {self.allowed_projections}')
        elif c_proj == "EPSG:4326":
            point = QgsPoint(point)
            point.transform(self.pj_transformer)
            point = QgsPointXY(point)

        nearest_id = self.index.nearestNeighbor(point, 1)

        request = QgsFeatureRequest()
        request.setFilterFids(nearest_id)

        #TODO: Check if vector layer is activated!
        features = self.iface.activeLayer().getFeatures(request)

        # https://qgis.org/pyqgis/master/core/QgsSpatialIndex.html?highlight=spatialindex#module-QgsSpatialIndex
        elem = next(features, False)

        if not elem:
            raise Exception ("No pub close")

        #TODO: Check if feature has Name attribute!
        return elem.attribute("Name")    

    def handle_click(self, point):

        try:
            nearest = self.get_nearest_point_name(point)

            msg = f'You are at x: {point.x()} y: {point.y()}\
                \nNearest point to you: {nearest}'
            QMessageBox.information(None, 'Pub Tool', msg)

        except Exception as ex:
            self.iface.messageBar().pushMessage("Error", str(ex), level=Qgis.Critical)