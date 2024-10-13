# LaharZ

LaharZ is an open source tool which can be used to model various flow hazards, most significantly lahars, based on a digital elevation model (DEM). From the DEM, LaharZ creates a stream file (which defines stream thalwegs), a flow direction file, an energy cone based on a height/length (H/L) ration, a set of initiation points (which can be edited) and a set of flows based on a range of volumes.

Stream and flow files created on any appropriate GIS system can be accepted instead of those generated and the resulting flows can similarly be displayed on any GIS system. However, LaharZ has been written and tested using QGIS and this guide will be based on QGIS .

The graphics produced can be displayed on any visualisation tool (including QGIS’s 3D mapping tool). However, LaharZ has been written and tested using Paraview for 3D graphics and this guide will be based on Paraview .

The programme is based on Schilling, S.P., 1998 [1].

Keith Blair
laharz@hotmail.com
October 2024
Version 2.1.4a


