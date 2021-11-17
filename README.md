# LaharZ
LAHARZ creates a series of lahar tif files which can then be loaded into QGIS. The lahars are based on the volumes the user inputs and the initiation points are determined from the energy cone, based on the H/L ratio.  

laharz@hotmail.com
Nov 2021

Laharz Python Program
•	Collects user parameters
•	Opens DEM, Stream and Flow files
•	Determines the energy cone based on the H/L ratio input
•	Determines the initiation points where the thalwegs meet the energy cone
•	For each initiation point and volume selected, creates a separate file for the lahar flow. Separate files are created for all initiation points for a volume and for all initiation points for all volumes
•	Files are also output for the thalwegs, energy cone (raw, filled and line) and the initiation points
