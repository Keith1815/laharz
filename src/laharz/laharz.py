# Version 1.0.0 Released: 14/11/21

# Keith Blair
# laharz@hotmail.com
# License Apache 2.0
# ==================================================================================================================================================================================
#LaharZ v0.3 - working
#Laharz v0.4 - temporary version - not tested
#Laharz v0.5 - based on LaharZ3 - working
#Laharz v0.6 - using points, volume and total summaries - working
#Laharz v0.7 - rework section area - working
#Laharz v0.8 - add graphic of crosssection, working but tidied up parameters
#Laharz v0.9 - add reading of tif files directly - not finished
#Laharz v0.10 - add reading of tif files directly and adding in pyproj
#Laharz v0.11 - general tidy up and restructure
#Laharz v0.12 - moving to use QGIS r.stream.extract for thalwegs and flow direction. Dropping Accumulation file. Dropping Channel Paths. Removing old routines replaced by pyproj.
#Laharz v0.13 - adding in projection of landscape and energy cone. General tidy up
#Laharz v0.14 - adding in screen for parameters. Intermediate version
#Laharz v0.15 - adding in screen for parameters
#Laharz v0.16 - minor fixes; scroll bars for window
#Laharz v1.0.0 - first public release
#Laharz v1.0.1 - improved method for finding the energy cone. Significantly faster. Some corrections to obscure conditions when determining the initiation points

#==================================================================================================================================================================================

#imports
from rasterio.rio.helpers import resolve_inout
from scipy.ndimage import binary_erosion, binary_fill_holes
import csv
import datetime
import gmsh
import numpy as np
import os
import pickle
import pyproj
import rasterio as rio
import simplekml
import sys
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageFont

# import tqdm

# Global ##########################################################################################################
#global dem_f, dem_crs

# Classes ##########################################################################################################

# XMing must be running
class Application(tk.Frame):
    """Main Application Frame"""
    pwdir = 'Working Directory'
    pdem_fn = 'dem.tif'
    pthal_fn = 'stream.tif'
    pflow_fn = 'flow.tif'
    pvolume = '1e5, 1e6'
    phlratio = 0.2
    ppeak_entry = '16.05, 61.66'
    phprange = 5000
    psealevel = 0
    plahar_dir = 'lahar'
    pinitpoints_fn = 'initpoints.csv'
    plog_fn = 'log.txt'
    pecraw_fn = 'ecraw.tif'
    pecfilled_fn = 'ecfilled.tif'
    pecline_fn = 'ecline.tif'
    pplotmesh = False
    pmesh_dir = 'mesh'
    pmeshres = 200
    pmeshsize = 1.3
    pcalcinitpoints = 'calc'
    puserowcol = 'True'
    piponly = 'n'
    
    pwdir_prev = 'Guad'
    pdem_fn_prev = 'dem.tif'
    pthal_fn_prev = 'stream.tif'
    pflow_fn_prev = 'flow.tif'
    pvolume_prev = '1e5, 1e6'
    phlratio_prev = 0.2
    ppeak_entry_prev = '16.05, 61.66'
    phprange_prev = 5000
    psealevel_prev = 0
    plahar_dir_prev = 'lahar'
    pinitpoints_fn_prev = 'initpoints.csv'
    plog_fn_prev = 'log.txt'
    pecraw_fn_prev = 'ecraw.tif'
    pecfilled_fn_prev = 'ecfilled.tif'
    pecline_fn_prev = 'ecline.tif'
    pplotmesh_prev = False
    pmesh_dir_prev = 'mesh'
    pmeshres_prev = 200
    pmeshsize_prev = 1.3
    pcalcinitpoints_prev = 'calc'
    puserowcol_prev = 'True'
    piponly_prev = 'n'
    
    pparameters = {}

    def __init__(self, master):
        """initialise the frame"""
        tk.Frame.__init__(self, master)
        # self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")
        self.canvas = tk.Canvas(self, borderwidth=0)
        # self.frame = tk.Frame(self.canvas, background="#ffffff")
        self.frame = tk.Frame(self.canvas)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((20,20), window=self.frame, anchor="nw", tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)

        self.create_widgets()

    def create_widgets(self):
        # LaharZ
        tk.Label(self.frame, text='LaharZ', font=('Helvetica', 14, 'bold')).grid(row=0, column=0, columnspan=2, sticky='W')

        # Blank line
        tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=1, column=0, columnspan=2, sticky='W')

        # Working Directory
        tk.Label(self.frame, text='Working Directory', font=('Helvetica', 12)).grid(row=2, column=0, columnspan=2, sticky='W')
        self.tk_pwdir = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pwdir.grid(row=2, column=3, columnspan=2, sticky='W')
        self.tk_pwdir.insert(0, self.pwdir)
        self.tk_pwdir_msg = tk.Label(self.frame, text='Working directory for this run. Should contain the input files. ', font=('Helvetica', 12))
        self.tk_pwdir_msg.grid(row=2, column=9, columnspan=4, sticky='W')

        # Load Parameters
        tk.Label(self.frame, text='Load Parameters', font=('Helvetica', 12)).grid(row=3, column=0, columnspan=2, sticky='W')
        self.tk_pload_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pload_fn.grid(row=3, column=3, columnspan=2, sticky='W')
        self.tk_pload_fn.insert(0, "parameters.pickle")
        self.tk_pload_fn_msg = tk.Label(self.frame, text='File name of where you load the parameters from, if you wish to ', font=('Helvetica', 12))
        self.tk_pload_fn_msg.grid(row=3, column=9, columnspan=4, sticky='W')

        # Load
        self.tk_load_params = tk.Button(self.frame, text='Load', font=('Helvetica', 12))
        self.tk_load_params.grid(row=3, column=6, columnspan=2, sticky='W')
        self.tk_load_params['command'] = self.load_params

        # Blank line
        tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=4, column=0, columnspan=2, sticky='W')

        # Inputs
        tk.Label(self.frame, text='Inputs', font=('Helvetica', 14, 'bold')).grid(row=5, column=0, columnspan=2, sticky='W')

        # DEM File
        tk.Label(self.frame, text='DEM File', font=('Helvetica', 12)).grid(row=6, column=0, columnspan=2, sticky='W')
        self.tk_pdem_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pdem_fn.grid(row=6, column=3, columnspan=2, sticky='W')
        self.tk_pdem_fn.insert(0, self.pdem_fn)
        self.tk_pdem_fn_msg = tk.Label(self.frame, text='Name of your DEM file in your working directory ', font=('Helvetica', 12))
        self.tk_pdem_fn_msg.grid(row=6, column=9, columnspan=4, sticky='W')

        # Stream File
        tk.Label(self.frame, text='Stream File', font=('Helvetica', 12)).grid(row=7, column=0, columnspan=2, sticky='W')
        self.tk_pthal_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pthal_fn.grid(row=7, column=3, columnspan=2, sticky='W')
        self.tk_pthal_fn.insert(0, self.pthal_fn)
        self.tk_pthal_fn_msg = tk.Label(self.frame, text='Name of your Stream file in your working directory ', font=('Helvetica', 12))
        self.tk_pthal_fn_msg.grid(row=7, column=9, columnspan=4, sticky='W')

        # Flow File
        tk.Label(self.frame, text='Flow File', font=('Helvetica', 12)).grid(row=8, column=0, columnspan=2, sticky='W')
        self.tk_pflow_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pflow_fn.grid(row=8, column=3, columnspan=2, sticky='W')
        self.tk_pflow_fn.insert(0, self.pflow_fn)
        self.tk_pflow_fn_msg = tk.Label(self.frame, text='Name of your Flow file in your working directory ', font=('Helvetica', 12))
        self.tk_pflow_fn_msg.grid(row=8, column=9, columnspan=4, sticky='W')

        # Volume
        tk.Label(self.frame, text='Volume', font=('Helvetica', 12)).grid(row=9, column=0, columnspan=2, sticky='W')
        self.tk_pvolume = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pvolume.grid(row=9, column=3, columnspan=2, sticky='W')
        self.tk_pvolume.insert(0, self.pvolume)
        self.tk_pvolume_msg = tk.Label(self.frame, text='Volumes (m^3) in a list separated by commas ', font=('Helvetica', 12))
        self.tk_pvolume_msg.grid(row=9, column=9, columnspan=4, sticky='W')

        # H/L Ratio
        tk.Label(self.frame, text='H/L Ratio', font=('Helvetica', 12)).grid(row=10, column=0, columnspan=2, sticky='W')
        self.tk_phlratio = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_phlratio.grid(row=10, column=3, columnspan=2, sticky='W')
        self.tk_phlratio.insert(0, self.phlratio)
        self.tk_phlratio_msg = tk.Label(self.frame, text='H/L Ratios normally between 0.2 and 0.3 ', font=('Helvetica', 12))
        self.tk_phlratio_msg.grid(row=10, column=9, columnspan=4, sticky='W')

        # Peak
        tk.Label(self.frame, text='Peak', font=('Helvetica', 12)).grid(row=11, column=0, columnspan=2, sticky='W')
        self.tk_ppeak_entry = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_ppeak_entry.grid(row=11, column=3, columnspan=2, sticky='W')
        self.tk_ppeak_entry.insert(0, self.ppeak_entry)
        self.tk_ppeak_entry_msg = tk.Label(self.frame, text='Approximate latitude and longitude of the peak ', font=('Helvetica', 12))
        self.tk_ppeak_entry_msg.grid(row=11, column=9, columnspan=4, sticky='W')

        # Search Diagonal
        tk.Label(self.frame, text='Search Diagonal', font=('Helvetica', 12)).grid(row=12, column=0, columnspan=2, sticky='W')
        self.tk_phprange = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_phprange.grid(row=12, column=3, columnspan=2, sticky='W')
        self.tk_phprange.insert(0, self.phprange)
        self.tk_phprange_msg = tk.Label(self.frame, text='Length of search diagonal in m ', font=('Helvetica', 12))
        self.tk_phprange_msg.grid(row=12, column=9, columnspan=4, sticky='W')

        # Sea Level
        tk.Label(self.frame, text='Sea Level', font=('Helvetica', 12)).grid(row=13, column=0, columnspan=2, sticky='W')
        self.tk_psealevel = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_psealevel.grid(row=13, column=3, columnspan=2, sticky='W')
        self.tk_psealevel.insert(0, self.psealevel)
        self.tk_psealevel_msg = tk.Label(self.frame, text='Sea Level in m ', font=('Helvetica', 12))
        self.tk_psealevel_msg.grid(row=13, column=9, columnspan=4, sticky='W')

        # Blank line
        tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=14, column=0, columnspan=2, sticky='W')

        # Outputs
        tk.Label(self.frame, text='Outputs', font=('Helvetica', 14, 'bold')).grid(row=15, column=0, columnspan=2, sticky='W')

        # Lahar Directory
        tk.Label(self.frame, text='Lahar Directory', font=('Helvetica', 12)).grid(row=16, column=0, columnspan=2, sticky='W')
        self.tk_plahar_dir = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_plahar_dir.grid(row=16, column=3, columnspan=2, sticky='W')
        self.tk_plahar_dir.insert(0, self.plahar_dir)
        self.tk_plahar_dir_msg = tk.Label(self.frame, text='Directory which contains the lahar files in your working directory ', font=('Helvetica', 12))
        self.tk_plahar_dir_msg.grid(row=16, column=9, columnspan=4, sticky='W')

        # Initiation Points
        tk.Label(self.frame, text='Initiation Points', font=('Helvetica', 12)).grid(row=17, column=0, columnspan=2, sticky='W')
        self.tk_pinitpoints_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pinitpoints_fn.grid(row=17, column=3, columnspan=2, sticky='W')
        self.tk_pinitpoints_fn.insert(0, self.pinitpoints_fn)
        self.tk_pinitpoints_fn_msg = tk.Label(self.frame, text='File name of the initiation points ', font=('Helvetica', 12))
        self.tk_pinitpoints_fn_msg.grid(row=17, column=9, columnspan=4, sticky='W')

        # Log File
        tk.Label(self.frame, text='Log File', font=('Helvetica', 12)).grid(row=18, column=0, columnspan=2, sticky='W')
        self.tk_plog_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_plog_fn.grid(row=18, column=3, columnspan=2, sticky='W')
        self.tk_plog_fn.insert(0, self.plog_fn)
        self.tk_plog_fn_msg = tk.Label(self.frame, text='File name of the log of all details ', font=('Helvetica', 12))
        self.tk_plog_fn_msg.grid(row=18, column=9, columnspan=4, sticky='W')

        # Raw Energy Cone
        tk.Label(self.frame, text='Raw Energy Cone', font=('Helvetica', 12)).grid(row=19, column=0, columnspan=2, sticky='W')
        self.tk_pecraw_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pecraw_fn.grid(row=19, column=3, columnspan=2, sticky='W')
        self.tk_pecraw_fn.insert(0, self.pecraw_fn)
        self.tk_pecraw_fn_msg = tk.Label(self.frame, text='File name of the Raw Energy Cone ', font=('Helvetica', 12))
        self.tk_pecraw_fn_msg.grid(row=19, column=9, columnspan=4, sticky='W')

        # Filled Energy Cone
        tk.Label(self.frame, text='Filled Energy Cone', font=('Helvetica', 12)).grid(row=20, column=0, columnspan=2, sticky='W')
        self.tk_pecfilled_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pecfilled_fn.grid(row=20, column=3, columnspan=2, sticky='W')
        self.tk_pecfilled_fn.insert(0, self.pecfilled_fn)
        self.tk_pecfilled_fn_msg = tk.Label(self.frame, text='File name of the Filled Energy Cone ', font=('Helvetica', 12))
        self.tk_pecfilled_fn_msg.grid(row=20, column=9, columnspan=4, sticky='W')

        # Energy Cone Line
        tk.Label(self.frame, text='Energy Cone Line', font=('Helvetica', 12)).grid(row=21, column=0, columnspan=2, sticky='W')
        self.tk_pecline_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pecline_fn.grid(row=21, column=3, columnspan=2, sticky='W')
        self.tk_pecline_fn.insert(0, self.pecline_fn)
        self.tk_pecline_fn_msg = tk.Label(self.frame, text='File name of the Energy Cone Line ', font=('Helvetica', 12))
        self.tk_pecline_fn_msg.grid(row=21, column=9, columnspan=4, sticky='W')

        # Blank line
        tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=22, column=0, columnspan=2, sticky='W')

        # Mesh
        tk.Label(self.frame, text='Mesh', font=('Helvetica', 14, 'bold')).grid(row=23, column=0, columnspan=2, sticky='W')

        # Plot Mesh
        self.tk_pplotmesh = tk.BooleanVar(value = self.pplotmesh)
        tk.Checkbutton(self.frame, text='Plot Mesh', font=('Helvetica', 12), variable=self.tk_pplotmesh).grid(row=24, column=0, columnspan=2, sticky='W')
        self.tk_pplotmesh_msg = tk.Label(self.frame, text='Check if you wish to create 3D mesh files ', font=('Helvetica', 12))
        self.tk_pplotmesh_msg.grid(row=24, column=9, columnspan=4, sticky='W')

        # Mesh Directory
        tk.Label(self.frame, text='Mesh Directory', font=('Helvetica', 12)).grid(row=25, column=0, columnspan=2, sticky='W')
        self.tk_pmesh_dir = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pmesh_dir.grid(row=25, column=3, columnspan=2, sticky='W')
        self.tk_pmesh_dir.insert(0, self.pmesh_dir)
        self.tk_pmesh_dir_msg = tk.Label(self.frame, text='Directory which contains the mesh files in your working directory ', font=('Helvetica', 12))
        self.tk_pmesh_dir_msg.grid(row=25, column=9, columnspan=4, sticky='W')

        # Mesh Resolution
        tk.Label(self.frame, text='Mesh Resolution', font=('Helvetica', 12)).grid(row=26, column=0, columnspan=2, sticky='W')
        self.tk_pmeshres = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pmeshres.grid(row=26, column=3, columnspan=2, sticky='W')
        self.tk_pmeshres.insert(0, self.pmeshres)
        self.tk_pmeshres_msg = tk.Label(self.frame, text='Mesh resolution (number of points in x & y direction) ', font=('Helvetica', 12))
        self.tk_pmeshres_msg.grid(row=26, column=9, columnspan=4, sticky='W')

        # Mesh Extent
        tk.Label(self.frame, text='Mesh Extent', font=('Helvetica', 12)).grid(row=27, column=0, columnspan=2, sticky='W')
        self.tk_pmeshsize = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_pmeshsize.grid(row=27, column=3, columnspan=2, sticky='W')
        self.tk_pmeshsize.insert(0, self.pmeshsize)
        self.tk_pmeshsize_msg = tk.Label(self.frame, text='What extent to plot the mesh (1.3 = 130% of the area of the energy cone line) ', font=('Helvetica', 12))
        self.tk_pmeshsize_msg.grid(row=27, column=9, columnspan=4, sticky='W')

        # Blank line
        tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=28, column=0, columnspan=2, sticky='W')

        # Controls
        tk.Label(self.frame, text='Controls', font=('Helvetica', 14, 'bold')).grid(row=29, column=0, columnspan=2, sticky='W')

        # Control Radio Buttons
        self.tk_pcalcinitpoints = tk.StringVar()
        self.tk_pcalcinitpoints.set(self.pcalcinitpoints)

        # Calculate Initiation Ponts
        tk.Radiobutton(self.frame, text='Calculate Initiation Ponts', font=('Helvetica', 12), variable=self.tk_pcalcinitpoints, value='calc').grid(row=30, column=0, columnspan=2, sticky='W')

        # Load Initiation Points
        tk.Radiobutton(self.frame, text='Load Initiation Points', font=('Helvetica', 12), variable=self.tk_pcalcinitpoints, value='load').grid(row=31, column=0, columnspan=2, sticky='W')

        # Use Row/Col
        self.tk_puserowcol = tk.BooleanVar(value=self.puserowcol)
        tk.Checkbutton(self.frame, text='Use Row/Col', font=('Helvetica', 12), variable=self.tk_puserowcol).grid(row=32, column=0, columnspan=2, sticky='W')
        self.tk_puserowcol_msg = tk.Label(self.frame, text='Check to use rows and columns if loading initiation points; otherwise uses latitude and longitude ', font=('Helvetica', 12))
        self.tk_puserowcol_msg.grid(row=32, column=9, columnspan=4, sticky='W')

        # Initiation Points Only
        self.tk_piponly = tk.BooleanVar()
        tk.Checkbutton(self.frame, text='Initiation Points Only', font=('Helvetica', 12), variable=self.tk_piponly).grid(row=33, column=0, columnspan=2, sticky='W')

        # Blank line
        tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=34, column=0, columnspan=2, sticky='W')

        # Save Parameters
        tk.Label(self.frame, text='Save Parameters', font=('Helvetica', 12)).grid(row=35, column=0, columnspan=2, sticky='W')
        self.tk_psave_fn = tk.Entry(self.frame, font=('Helvetica', 12))
        self.tk_psave_fn.grid(row=35, column=3, columnspan=2, sticky='W')
        self.tk_psave_fn.insert(0, "parameters.pickle")
        self.tk_psave_fn_msg = tk.Label(self.frame, text='File name of where you load the parameters from, if you wish to ', font=('Helvetica', 12))
        self.tk_psave_fn_msg.grid(row=35, column=9, columnspan=4, sticky='W')

        # Save
        self.tk_save_params = tk.Button(self.frame, text='Save', font=('Helvetica', 12))
        self.tk_save_params.grid(row=35, column=6, columnspan=2, sticky='W')
        self.tk_save_params['command'] = self.save_params

        # Submit
        self.tk_submit = tk.Button(self.frame, text='Submit', font=('Helvetica', 12))
        self.tk_submit.grid(row=36, column=0, columnspan=2, sticky='W')
        self.tk_submit['command'] = self.submit

        # Status
        self.tk_statusmsg = tk.Label(self.frame, font=('Helvetica', 12))
        self.tk_statusmsg.grid(row=37, column=0, columnspan=12, sticky='W')

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def submit(self):
        error = False
        change = False
        warning = False

        # Validate tk_pwdir
        pwdir = self.tk_pwdir.get()
        if pwdir != self.pwdir_prev:
            change = True
            self.pwdir_prev = pwdir
        if os.path.isdir("../" + pwdir) and pwdir != "":
            self.tk_pwdir_msg['text'] = ""
            self.pwdir = pwdir
        else:
            self.tk_pwdir_msg['text'] = "Error: Directory does not exist"
            self.tk_pwdir_msg['fg'] = "red"

            error = True
        
        # Validate tk_pdem_fn
        pdem_fn = self.tk_pdem_fn.get()
        if pdem_fn != self.pdem_fn_prev:
            change = True
            self.pdem_fn_prev = pdem_fn
        pdem_fn = "../" + pwdir + "/" + pdem_fn
        if os.path.isfile(pdem_fn):
            self.tk_pdem_fn_msg['text'] = ""
            self.pdem_fn = pdem_fn
        else:
            self.tk_pdem_fn_msg['text'] = "Error: File does not exist"
            self.tk_pdem_fn_msg['fg'] = "red"
            error = True

        # Validate tk_pthal_fn
        pthal_fn = self.tk_pthal_fn.get()
        if pthal_fn != self.pthal_fn_prev:
            change = True
            self.pthal_fn_prev = pthal_fn
        pthal_fn = "../" + pwdir + "/" + pthal_fn
        if os.path.isfile(pthal_fn):
            self.tk_pthal_fn_msg['text'] = ""
            self.pthal_fn = pthal_fn
        else:
            self.tk_pthal_fn_msg['text'] = "Error: File does not exist"
            self.tk_pthal_fn_msg['fg'] = "red"
            error = True


        # Validate tk_pflow_fn
        pflow_fn = self.tk_pflow_fn.get()
        if pflow_fn != self.pflow_fn_prev:
            change = True
            self.pflow_fn_prev = pflow_fn
        pflow_fn = "../" + pwdir + "/" + pflow_fn
        if os.path.isfile(pflow_fn):
            self.tk_pflow_fn_msg['text'] = ""
            self.pflow_fn = pflow_fn
        else:
            self.tk_pflow_fn_msg['text'] = "Error: File does not exist"
            self.tk_pflow_fn_msg['fg'] = "red"
            error = True

        # Validate tk_pvolume
        pvolume = self.tk_pvolume.get()
        if pvolume != self.pvolume_prev:
            change = True
            self.pvolume_prev = pvolume
        #convert to numeric
        pvolume = self.tk_pvolume.get().split(",")
        pvolume2 = []
        pvolume_error = False
        for i in pvolume:
            try:
                pvolume2 += [float(i),]
            except:
                self.tk_pvolume_msg['text'] = "Error: Values must be numeric"
                self.tk_pvolume_msg['fg'] = "red"
                error = True
                pvolume_error = True
                break
        if not pvolume_error:
            self.tk_pvolume_msg['text'] = ""
            pvolume = pvolume2
            for i in pvolume:
                    if i<1e4 or i>1e12:
                        self.tk_pvolume_msg['text'] = "Warning: Values outside of normal range of 1e4 - 1e12"
                        self.tk_pvolume_msg['fg'] = "#b36b00"
                        warning = True
                        break
            self.pvolume = pvolume

        # Validate tk_phlratio
        phlratio = self.tk_phlratio.get()
        if phlratio != self.phlratio_prev:
            change = True
            self.phlratio_prev = phlratio
        phlratio_error = False
        try:
            phlratio = float(phlratio)
        except:
            self.tk_phlratio_msg['text'] = "Error: Value must be numeric"
            self.tk_phlratio_msg['fg'] = "red"
            error = True
            phlratio_error = True
        if not phlratio_error:
            self.tk_phlratio_msg['text'] = ""
            if phlratio < 0.2 or phlratio > 0.3:
                self.tk_phlratio_msg['text'] = "Warning: Values outside of normal range of 0.2 - 0.3"
                self.tk_phlratio_msg['fg'] = "#b36b00"
                warning = True
        self.phlratio = phlratio

        # Validate tk_ppeak_entry
        ppeak_entry = self.tk_ppeak_entry.get().split(",")
        if ppeak_entry != self.ppeak_entry_prev:
            change = True
            self.ppeak_entry_prev = ppeak_entry
        #convert to numeric
        ppeak_entry = self.tk_ppeak_entry.get().split(",")
        ppeak_entry2 = []
        ppeak_entry_error = False
        for i in ppeak_entry:
            try:
                ppeak_entry2 += [float(i),]
            except:
                self.tk_ppeak_entry_msg['text'] = "Error: Values must be numeric"
                self.tk_ppeak_entry_msg['fg'] = "red"
                error = True
                ppeak_entry_error = True
                break

        if not ppeak_entry_error:
            self.tk_ppeak_entry_msg['text'] = ""
            ppeak_entry = ppeak_entry2
            self.ppeak_entry = ppeak_entry
            if len(ppeak_entry) != 2:
                self.tk_ppeak_entry_msg['text'] = "Error: Only 2 values (Latitude and Longitude) accepted"
                self.tk_ppeak_entry_msg['fg'] = "red"
                error = True
            else:
                if ppeak_entry[0] <-90 or ppeak_entry[0]>90:
                    self.tk_ppeak_entry_msg['text'] = "Error: Latitude outside of normal range of -90 to 90 degrees"
                    self.tk_ppeak_entry_msg['fg'] = "red"
                    error = True
                if ppeak_entry[1] <-180 or ppeak_entry[0]>180:
                    self.tk_ppeak_entry_msg['text'] = "Error: Longitude outside of normal range of -180 to 180 degrees"
                    self.tk_ppeak_entry_msg['fg'] = "red"
                    error = True

        # Validate tk_phprange
        phprange = self.tk_phprange.get()
        if phprange != self.phprange_prev:
            self.phprange_prev = phprange
            change = True
        try:
            phprange = float(phprange)
            self.tk_phprange_msg['text'] = ""
        except:
            self.tk_phprange_msg['text'] = "Error: Value must be numeric"
            self.tk_phprange_msg['fg'] = "red"
            error = True
        self.phprange = phprange

        # Validate tk_psealevel
        psealevel = self.tk_psealevel.get()
        if psealevel != self.psealevel_prev:
            self.psealevel_prev = psealevel
            change = True
        try:
            psealevel = float(psealevel)
            self.tk_psealevel_msg['text'] = ""
        except:
            self.tk_psealevel_msg['text'] = "Error: Value must be numeric"
            self.tk_psealevel_msg['fg'] = "red"
            error = True
        self.psealevel = psealevel

        # Validate tk_plahar_dir
        plahar_dir = self.tk_plahar_dir.get()
        if plahar_dir != self.plahar_dir_prev:
            self.plahar_dir_prev = plahar_dir
            change = True
        if not plahar_dir.isalnum():
            self.tk_plahar_dir_msg['text'] = "Error: Value must be alphanumeric"
            self.tk_plahar_dir_msg['fg'] = "red"
            error = True
        else:
            self.tk_plahar_dir_msg['text'] = ""
            self.plahar_dir = plahar_dir

        # Validate tk_pinitpoints_fn
        pinitpoints_fn = self.tk_pinitpoints_fn.get()
        if pinitpoints_fn != self.pinitpoints_fn_prev:
            change = True
            self.pinitpoints_fn_prev = pinitpoints_fn
        pinitpoints_fn = self.tk_pinitpoints_fn.get().split(".")
        if len(pinitpoints_fn)!=2:
            self.tk_pinitpoints_fn_msg['text'] = "Error: Invalid file format"
            self.tk_pinitpoints_fn_msg['fg'] = "red"
            error = True
        elif not pinitpoints_fn[0].isalnum():
            self.tk_pinitpoints_fn_msg['text'] = "Error: Invalid file format"
            self.tk_pinitpoints_fn_msg['fg'] = "red"
            error = True
        elif pinitpoints_fn[1] !="csv":
            self.tk_pinitpoints_fn_msg['text'] = "Error: csv extension only"
            self.tk_pinitpoints_fn_msg['fg'] = "red"
            error = True
        else:
            self.tk_pinitpoints_fn_msg['text'] = ""
        self.pinitpoints_fn = self.tk_pinitpoints_fn.get()


        # Validate tk_plog_fn
        plog_fn = self.tk_plog_fn.get()
        if plog_fn != self.plog_fn_prev:
            change = True
            self.plog_fn_prev = plog_fn
        plog_fn = self.tk_plog_fn.get().split(".")
        if len(plog_fn)!=2:
            self.tk_plog_fn_msg['text'] = "Error: Invalid file format"
            self.tk_plog_fn_msg['fg'] = "red"
            error = True
        elif not plog_fn[0].isalnum():
            self.tk_plog_fn_msg['text'] = "Error: Invalid file format"
            self.tk_plog_fn_msg['fg'] = "red"
            error = True
        elif plog_fn[1] !="txt":
            self.tk_plog_fn_msg['text'] = "Error: txt extension only"
            self.tk_plog_fn_msg['fg'] = "red"
            error = True
        else:
            self.tk_plog_fn_msg['text'] = ""
        self.plog_fn = self.tk_plog_fn.get()
        
        # Validate tk_pecraw_fn
        pecraw_fn = self.tk_pecraw_fn.get()
        if pecraw_fn != self.pecraw_fn_prev:
            change = True
            self.pecraw_fn_prev = pecraw_fn
        pecraw_fn = self.tk_pecraw_fn.get().split(".")
        if len(pecraw_fn)!=2:
            self.tk_pecraw_fn_msg['text'] = "Error: Invalid file format"
            self.tk_pecraw_fn_msg['fg'] = "red"
            error = True
        elif not pecraw_fn[0].isalnum():
            self.tk_pecraw_fn_msg['text'] = "Error: Invalid file format"
            self.tk_pecraw_fn_msg['fg'] = "red"
            error = True
        elif pecraw_fn[1] !="tif":
            self.tk_pecraw_fn_msg['text'] = "Error: tif extension only"
            self.tk_pecraw_fn_msg['fg'] = "red"
            error = True
        else:
            self.tk_pecraw_fn_msg['text'] = ""
        self.pecraw_fn = self.tk_pecraw_fn.get()
        
        # Validate tk_pecfilled_fn
        pecfilled_fn = self.tk_pecfilled_fn.get()
        if pecfilled_fn != self.pecfilled_fn_prev:
            change = True
            self.pecfilled_fn_prev = pecfilled_fn
        pecfilled_fn = self.tk_pecfilled_fn.get().split(".")
        if len(pecfilled_fn)!=2:
            self.tk_pecfilled_fn_msg['text'] = "Error: Invalid file format"
            self.tk_pecfilled_fn_msg['fg'] = "red"
            error = True
        elif not pecfilled_fn[0].isalnum():
            self.tk_pecfilled_fn_msg['text'] = "Error: Invalid file format"
            self.tk_pecfilled_fn_msg['fg'] = "red"
            error = True
        elif pecfilled_fn[1] !="tif":
            self.tk_pecfilled_fn_msg['text'] = "Error: tif extension only"
            self.tk_pecfilled_fn_msg['fg'] = "red"
            error = True
        else:
            self.tk_pecfilled_fn_msg['text'] = ""
        self.pecfilled_fn = self.tk_pecfilled_fn.get()

        # Validate tk_pecline_fn
        pecline_fn = self.tk_pecline_fn.get()
        if pecline_fn != self.pecline_fn_prev:
            change = True
            self.pecline_fn_prev = pecline_fn
        pecline_fn = self.tk_pecline_fn.get().split(".")
        if len(pecline_fn)!=2:
            self.tk_pecline_fn_msg['text'] = "Error: Invalid file format"
            self.tk_pecline_fn_msg['fg'] = "red"
            error = True
        elif not pecline_fn[0].isalnum():
            self.tk_pecline_fn_msg['text'] = "Error: Invalid file format"
            self.tk_pecline_fn_msg['fg'] = "red"
            error = True
        elif pecline_fn[1] !="tif":
            self.tk_pecline_fn_msg['text'] = "Error: tif extension only"
            self.tk_pecline_fn_msg['fg'] = "red"
            error = True
        else:
            self.tk_pecline_fn_msg['text'] = ""
        self.pecline_fn = self.tk_pecline_fn.get()

        # Validate tk_pplotmesh
        pplotmesh = self.tk_pplotmesh.get()
        if pplotmesh != self.pplotmesh_prev:
            change = True
            self.pplotmesh_prev = pplotmesh
        self.tk_pplotmesh_msg['text'] = ""
        self.pplotmesh = pplotmesh

        # Validate tk_pmesh_dir
        pmesh_dir = self.tk_pmesh_dir.get()
        if pmesh_dir != self.pmesh_dir_prev:
            change = True
            self.pmesh_dir_prev = pmesh_dir
        if not pmesh_dir.isalnum():
            self.tk_pmesh_dir_msg['text'] = "Error: Value must be alphanumeric"
            self.tk_pmesh_dir_msg['fg'] = "red"
            error = True
        else:
            self.tk_pmesh_dir_msg['text'] = ""
            self.pmesh_dir = pmesh_dir

        # Validate tk_pmeshres
        pmeshres = self.tk_pmeshres.get()
        if pmeshres != self.pmeshres_prev:
            change = True
            self.pmeshres_prev = pmeshres
        try:
            pmeshres = int(pmeshres)
            self.tk_pmeshres_msg['text'] = ""
            self.pmeshres = pmeshres
        except:
            self.tk_pmeshres_msg['text'] = "Error: Value must an integer. Usually 50 - 400"
            self.tk_pmeshres_msg['fg'] = "red"
            error = True

        # Validate tk_pmeshsize
        pmeshsize = self.tk_pmeshsize.get()
        if pmeshsize != self.pmeshsize_prev:
            change = True
            self.pmeshsize_prev = pmeshsize
        try:
            pmeshsize = float(pmeshsize)
            self.tk_pmeshsize_msg['text'] = ""
            self.pmeshsize = pmeshsize
        except:
            self.tk_pmeshsize_msg['text'] = "Error: Value must be numeric. Usually 1.3"
            self.tk_pmeshsize_msg['fg'] = "red"
            error = True

        # Validate tk_pcalcinitpoints
        pcalcinitpoints = self.tk_pcalcinitpoints.get()
        if pcalcinitpoints != self.pcalcinitpoints_prev:
            change = True
            self.pcalcinitpoints_prev = pcalcinitpoints
        self.pcalcinitpoints = pcalcinitpoints

        # Validate tk_puserowcol
        puserowcol = self.tk_puserowcol.get()
        if puserowcol != self.puserowcol_prev:
            change = True
            self.puserowcol_prev = puserowcol
        self.tk_puserowcol_msg['text'] = ""
        self.puserowcol = puserowcol

        # Validate tk_piponly
        piponly = self.tk_piponly.get()
        if piponly != self.piponly_prev:
            change = True
            self.piponly_prev = piponly
        self.piponly = piponly

        # Finalise
        if error:
            self.tk_statusmsg["text"] = "Errors exist"
            self.tk_statusmsg['fg'] = "red"
        elif warning and change:
            self.tk_statusmsg["text"] = "Warnings exist. Press submit to continue"
            self.tk_statusmsg['fg'] = "#b36b00"
        else:
            self.tk_statusmsg["text"] = "Lets go..."
            self.tk_statusmsg['fg'] = "black"
            self.update()
            self.uploaddict()
            laharz()

    def uploaddict(self):
        self.pparameters['pwdir'] = self.tk_pwdir.get()
        self.pparameters['pdem_fn'] = self.tk_pdem_fn.get()
        self.pparameters['pthal_fn'] = self.tk_pthal_fn.get()
        self.pparameters['pflow_fn'] = self.tk_pflow_fn.get()
        self.pparameters['pvolume'] = self.tk_pvolume.get()
        self.pparameters['phlratio'] = self.tk_phlratio.get()
        self.pparameters['ppeak_entry'] = self.tk_ppeak_entry.get()
        self.pparameters['phprange'] = self.tk_phprange.get()
        self.pparameters['psealevel'] = self.tk_psealevel.get()
        self.pparameters['plahar_dir'] = self.tk_plahar_dir.get()
        self.pparameters['pinitpoints_fn'] = self.tk_pinitpoints_fn.get()
        self.pparameters['plog_fn'] = self.tk_plog_fn.get()
        self.pparameters['pecraw_fn'] = self.tk_pecraw_fn.get()
        self.pparameters['pecfilled_fn'] = self.tk_pecfilled_fn.get()
        self.pparameters['pecline_fn'] = self.tk_pecline_fn.get()
        if self.tk_pplotmesh.get(): # bit bizarre but you can't pickle tkinter data
            self.pparameters['pplotmesh'] = True
        else:
            self.pparameters['pplotmesh'] = False
        self.pparameters['pmesh_dir'] = self.tk_pmesh_dir.get()
        self.pparameters['pmeshres'] = self.tk_pmeshres.get()
        self.pparameters['pmeshsize'] = self.tk_pmeshsize.get()
        self.pparameters['pcalcinitpoints'] = self.tk_pcalcinitpoints.get()
        if self.tk_puserowcol.get(): # bit bizarre but you can't pickle tkinter data
            self.pparameters['puserowcol'] = True
        else:
            self.pparameters['puserowcol'] = False
        if self.tk_piponly.get(): # bit bizarre but you can't pickle tkinter data
            self.pparameters['piponly'] = True
        else:
            self.pparameters['piponly'] = False

    def downloaddict(self):
        #update master variables
        self.pwdir = self.pparameters['pwdir']
        self.pdem_fn = self.pparameters['pdem_fn']
        self.pthal_fn = self.pparameters['pthal_fn']
        self.pflow_fn = self.pparameters['pflow_fn']
        self.pvolume = self.pparameters['pvolume']
        self.phlratio = self.pparameters['phlratio']
        self.ppeak_entry = self.pparameters['ppeak_entry']
        self.phprange = self.pparameters['phprange']
        self.psealevel = self.pparameters['psealevel']
        self.plahar_dir = self.pparameters['plahar_dir']
        self.pinitpoints_fn = self.pparameters['pinitpoints_fn']
        self.plog_fn = self.pparameters['plog_fn']
        self.pecraw_fn = self.pparameters['pecraw_fn']
        self.pecfilled_fn = self.pparameters['pecfilled_fn']
        self.pecline_fn = self.pparameters['pecline_fn']
        self.pplotmesh = self.pparameters['pplotmesh'] #boolean on boolean
        self.pmesh_dir = self.pparameters['pmesh_dir']
        self.pmeshres = self.pparameters['pmeshres']
        self.pmeshsize = self.pparameters['pmeshsize']
        self.pcalcinitpoints = self.pparameters['pcalcinitpoints']
        self.puserowcol = self.pparameters['puserowcol']
        self.piponly = self.pparameters['piponly']

        #update text variables
        self.tk_pwdir.delete(0, tk.END)
        self.tk_pdem_fn.delete(0, tk.END)
        self.tk_pthal_fn.delete(0, tk.END)
        self.tk_pflow_fn.delete(0, tk.END)
        self.tk_pvolume.delete(0, tk.END)
        self.tk_phlratio.delete(0, tk.END)
        self.tk_ppeak_entry.delete(0, tk.END)
        self.tk_phprange.delete(0, tk.END)
        self.tk_psealevel.delete(0, tk.END)
        self.tk_plahar_dir.delete(0, tk.END)
        self.tk_pinitpoints_fn.delete(0, tk.END)
        self.tk_plog_fn.delete(0, tk.END)
        self.tk_pecraw_fn.delete(0, tk.END)
        self.tk_pecfilled_fn.delete(0, tk.END)
        self.tk_pecline_fn.delete(0, tk.END)
        self.tk_pmesh_dir.delete(0, tk.END)
        self.tk_pmeshres.delete(0, tk.END)
        self.tk_pmeshsize.delete(0, tk.END)

        self.tk_pwdir.insert(0, self.pwdir)
        self.tk_pdem_fn.insert(0, self.pdem_fn)
        self.tk_pthal_fn.insert(0, self.pthal_fn)
        self.tk_pflow_fn.insert(0, self.pflow_fn)
        self.tk_pvolume.insert(0, self.pvolume)
        self.tk_phlratio.insert(0, self.phlratio)
        self.tk_ppeak_entry.insert(0, self.ppeak_entry)
        self.tk_phprange.insert(0, self.phprange)
        self.tk_psealevel.insert(0, self.psealevel)
        self.tk_plahar_dir.insert(0, self.plahar_dir)
        self.tk_pinitpoints_fn.insert(0, self.pinitpoints_fn)
        self.tk_plog_fn.insert(0, self.plog_fn)
        self.tk_pecraw_fn.insert(0, self.pecraw_fn)
        self.tk_pecfilled_fn.insert(0, self.pecfilled_fn)
        self.tk_pecline_fn.insert(0, self.pecline_fn)
        self.tk_pmesh_dir.insert(0, self.pmesh_dir)
        self.tk_pmeshres.insert(0, self.pmeshres)
        self.tk_pmeshsize.insert(0, self.pmeshsize)

        #update tk variables
        self.tk_pplotmesh.set(self.pparameters['pplotmesh'])
        self.tk_puserowcol.set(self.pparameters['puserowcol'])
        self.tk_piponly.set(self.pparameters['piponly'])
        self.tk_pcalcinitpoints.set(self.pparameters['pcalcinitpoints'])

    def load_params(self):
        pwdir = self.tk_pwdir.get()
        if os.path.isdir("../" + pwdir) and pwdir != "":
            self.tk_pwdir_msg['text'] = ""
            pload_fn = self.tk_pload_fn.get()
            pload_fn = "../" + pwdir + "/" + pload_fn
            if os.path.isfile(pload_fn):
                self.tk_pload_fn_msg['text'] = ""
                try:
                    self.pparameters = pickle.load(open(pload_fn, "rb"))
                except:
                    self.tk_pload_fn_msg['text'] = "Error: File does not appear to be a pickle file"
                    self.tk_pload_fn_msg['fg'] = "red"
                self.downloaddict()

            else:
                self.tk_pload_fn_msg['text'] = "Error: File does not exist"
                self.tk_pload_fn_msg['fg'] = "red"
        else:
            self.tk_pload_fn_msg['text'] = "Error: Specify valid working directory"
            self.tk_pload_fn_msg['fg'] = "red"
            self.tk_pwdir_msg['text'] = "Error: Directory does not exist"
            self.tk_pwdir_msg['fg'] = "red"

        pload_fn = self.tk_pload_fn.get()
        pload_fn = "../" + self.pwdir + "/" + pload_fn
        if os.path.isfile(pload_fn):
            try:
                self.pparameters = pickle.load(open(pload_fn, "rb"))
                self.downloaddict()
                self.tk_pwdir_msg["text"] = ''
                self.tk_pdem_fn_msg["text"] = ''
                self.tk_pthal_fn_msg["text"] = ''
                self.tk_pflow_fn_msg["text"] = ''
                self.tk_pvolume_msg["text"] = ''
                self.tk_phlratio_msg["text"] = ''
                self.tk_ppeak_entry_msg["text"] = ''
                self.tk_phprange_msg["text"] = ''
                self.tk_psealevel_msg["text"] = ''
                self.tk_plahar_dir_msg["text"] = ''
                self.tk_pinitpoints_fn_msg["text"] = ''
                self.tk_plog_fn_msg["text"] = ''
                self.tk_pecraw_fn_msg["text"] = ''
                self.tk_pecfilled_fn_msg["text"] = ''
                self.tk_pecline_fn_msg["text"] = ''
                self.tk_pplotmesh_msg["text"] = ''
                self.tk_pmesh_dir_msg["text"] = ''
                self.tk_pmeshres_msg["text"] = ''
                self.tk_pmeshsize_msg["text"] = ''
                self.tk_puserowcol_msg["text"] = ''
                self.tk_pload_fn_msg["text"] = ''
                self.tk_psave_fn_msg["text"] = ''
                self.tk_statusmsg["text"] = "Parameters Loaded"
                self.tk_statusmsg['fg'] = "black"
            except:
                self.tk_pload_fn_msg['text'] = "Error: File does not appear to be a pickle file"
                self.tk_pload_fn_msg['fg'] = "red"
        else:
            self.tk_pload_fn_msg['text'] = "Error: File does not exist"
            self.tk_pload_fn_msg['fg'] = "red"

    def save_params(self):
        def save_pickle(destroy = False):
            self.uploaddict()
            pickle.dump(self.pparameters, open(psave_fn, "wb"))

            self.tk_pwdir_msg["text"] = ''
            self.tk_pdem_fn_msg["text"] = ''
            self.tk_pthal_fn_msg["text"] = ''
            self.tk_pflow_fn_msg["text"] = ''
            self.tk_pvolume_msg["text"] = ''
            self.tk_phlratio_msg["text"] = ''
            self.tk_ppeak_entry_msg["text"] = ''
            self.tk_phprange_msg["text"] = ''
            self.tk_psealevel_msg["text"] = ''
            self.tk_plahar_dir_msg["text"] = ''
            self.tk_pinitpoints_fn_msg["text"] = ''
            self.tk_plog_fn_msg["text"] = ''
            self.tk_pecraw_fn_msg["text"] = ''
            self.tk_pecfilled_fn_msg["text"] = ''
            self.tk_pecline_fn_msg["text"] = ''
            self.tk_pplotmesh_msg["text"] = ''
            self.tk_pmesh_dir_msg["text"] = ''
            self.tk_pmeshres_msg["text"] = ''
            self.tk_pmeshsize_msg["text"] = ''
            self.tk_puserowcol_msg["text"] = ''
            self.tk_pload_fn_msg["text"] = ''
            self.tk_psave_fn_msg["text"] = ''
            self.tk_statusmsg["text"] = "Parameters Saved"
            self.tk_statusmsg['fg'] = "black"
            if destroy:
                window.destroy()

        # Validate tk_psave_fn
        psave_fn = self.tk_psave_fn.get().split(".")
        if len(psave_fn)!=2:
            self.tk_psave_fn_msg['text'] = "Error: Invalid file format"
            self.tk_psave_fn_msg['fg'] = "red"
            self.error = True
        elif not psave_fn[0].isalnum():
            self.tk_psave_fn_msg['text'] = "Error: Invalid file format"
            self.tk_psave_fn_msg['fg'] = "red"
            self.error = True
        elif psave_fn[1] !="pickle":
            self.tk_psave_fn_msg['text'] = "Error: pickle extension only"
            self.tk_psave_fn_msg['fg'] = "red"
            self.error = True
        else:
            pwdir = self.tk_pwdir.get()
            if os.path.isdir("../" + pwdir) and pwdir != "":
                self.pwdir = pwdir
                psave_fn = "../" + pwdir + "/" + self.tk_psave_fn.get()
                if os.path.isfile(psave_fn):
                    window = tk.Toplevel()
                    label1 = tk.Label(window, text="File already exists")
                    label1.pack(fill='x', padx=50, pady=5)
                    button_save = tk.Button(window, text="Save", command=lambda: save_pickle(destroy=True))
                    button_save.pack(fill='x')
                    button_cancel = tk.Button(window, text="Cancel", command=window.destroy)
                    button_cancel.pack(fill='x')
                else:
                    save_pickle()
            else:
                self.tk_psave_fn_msg['text'] = "Error: Specify valid working directory"
                self.tk_psave_fn_msg['fg'] = "red"
                self.tk_pwdir_msg['text'] = "Error: Directory does not exist"
                self.tk_pwdir_msg['fg'] = "red"


def laharz():
    class Point(object):
        # defines a 'Point' object which is any (row, column) pair on the cell matrix. The benefit of the class is to be
        # able to move to the next point in the matrix without worrying about reaching the edges. Using this class you can
        # add or subject from the point in any direction but if you reach the edge, the result will just be the point on
        # the edge. A warning will produce an warning message if the edge is reached. If the warning flag (which defaults
        # to "Y") is set to anything but "Y" o check on the boundary edge is not performed.

        def __init__(self, p):
            self.p = p

        def __str__(self):
            rep = "Point:" + str(self.p)
            return rep

        def plus(self, p, warn="Y"):
            r1 = self.p[0]
            r2 = p.p[0]
            c1 = self.p[1]
            c2 = p.p[1]

            if warn == "Y":
                r3 = min(r1 + r2, nrows - 1)
                r3 = max(r3, 0)  # in case of addition of negitive amount
                c3 = min(c1 + c2, ncols - 1)
                c3 = max(c3, 0)  # in case of addition of negitive amount
                if r1 + r2 > nrows - 1 or r1 + r2 < 0:
                    log_msg("Warning: potential overflow as {} is added to row {}".format(r2, r1))
                if c1 + c2 > ncols - 1 or c1 + c2 < 0:
                    log_msg("Warning: potential overflow as {} is added to column {}".format(c2, c1))
            else:
                r3 = r1 + r2
                c3 = c1 + c2
            return Point([r3, c3])

        def minus(self, p, warn="Y"):
            r1 = self.p[0]
            r2 = p.p[0]
            c1 = self.p[1]
            c2 = p.p[1]
            if warn == "Y":
                r3 = max(r1 - r2, 0)
                r3 = min(r3, nrows - 1)  # in case of subtraction of negitive amount
                c3 = max(c1 - c2, 0)
                c3 = min(c3, ncols - 1)
                if r1 - r2 > nrows - 1 or r1 - r2 < 0:
                    log_msg("Warning: potential overflow as {} is subtracted from row {}".format(r2, r1))
                if c1 - c2 > ncols - 1 or c1 - c2 < 0:
                    log_msg("Warning: potential overflow as {} is subtracted from column {}".format(c2, c1))
            else:
                r3 = r1 - r2
                c3 = c1 - c2
            return Point([r3, c3])

        def vector(self):
            """returns a list of the components of the point to allow it to be used for indexing numpy arrays"""
            return (self.p[0], self.p[1])

        def __eq__(self, other):
            if not isinstance(other, Point):
                # don't attempt to compare against unrelated types
                return NotImplemented
            return self.p == other.p

    # Functions
    def log_msg(msg, screen_op = True, file_op = True, errmsg = False, initfile = False):
        """logs message"""
        dt = datetime.datetime.now()
        if screen_op:
            app.tk_statusmsg["text"] = msg
            if not errmsg:
                app.tk_statusmsg["fg"] = "black"
            else:
                app.tk_statusmsg["fg"] = "red"
            app.update()
        msg = "{:02d}:{:02d}:{:02d}: ".format(dt.hour, dt.minute, dt.second) + msg
        if file_op:
            if initfile:
                f_log = open(plog_fn, 'w')
            else:
                f_log = open(plog_fn, 'a')
            f_log.write(msg +'\n')
            f_log.close
        #print(msg)

    def LoadFile(fn):
        """ Loads a .tif or text file (.asc or .txt)"""
        try:
            f = rio.open(fn)
        except:
            log_msg("File not found: " + fn)
            sys.exit() #shouldnt happen

        if fn[-3:] == "txt" or fn[-3] == "asc":  # ascii file
            fcrs = pyproj.Proj(ptextcrs)
        elif fn[-3:] == "tif":  # tif file
            fcrs = pyproj.Proj(f.crs)
        else:
            log_msg("Unrecognised file type for file name:{}. Terminating".format(fn))
            sys.exit() #shouldnt happen
        v = f.read(1)

        return f, fcrs, v

    def SaveFile(fn, ref_f, v):
        """ Saves a matrix as a .tif file, an Ascii file (.txt) or a .csv file"""
        # Although possible to save an as Ascii file there seems no particular reason to do so. Savingg as a csv file is convenient
        # for debugging. Recommend that the file is saved as a .tif file

        fn = fn.split(".")[0]
        # entry screen provides file names with extensions. These are ignored in program and the paramters pwritexxx are used instead to control output.
        # As the entry screen does not allow the user to enter the pwritexxx parameters, the pwritexxx parameters as specified in the program are for
        # tif files only. Adopting this method leaves an expert user to use the pwritexxx parameters in the program to control output and a general user
        # to rely on .tif files


        if pwritetif:
            resolve_inout(overwrite=True)
            profile = ref_f.profile
            # profile.update(dtype=rio.uint8, count=1, compress='lzw', nodata = 255)
            profile.update(dtype=rio.uint8, count=1, nodata=255)
            with rio.Env():
                with rio.open("../" + pwdir + "/" + fn + ".tif", 'w', **profile) as dst:
                    dst.write(v.astype(rio.uint8), 1)
        if pwriteascii:
            f = open("../" + pwdir + "/" + fn + ".txt", "w")
            f.write("ncols " + str(v.shape[1]) + "\n")
            f.write("nrows " + str(v.shape[0]) + "\n")
            row = col = 0
            east, north = ref_f.xy(row, col, offset='ll')  # spatial --> image coordinates
            lon, lat = dem_crs(east, north, inverse=True)
            f.write("xllcorner " + str(lon) + "\n")
            f.write("yllcorner " + str(lat) + "\n")
            f.write("cellsize " + str(ref_f.transform[0]) + "\n")
            f.write("NODATA_value 255")
            for i in reversed(v):
                f.write(" ".join(map(str, map(int, i))) + "\n")
            f.close()

        if pwritecsv:
            np.savetxt("../" + pwdir + "/" + fn + ".csv", v, delimiter=",")

    def AddPointKML(kml, ll, name):
        """Adds a point to a .kml file for display in Google Earth"""
        kml.newpoint(name=name, coords=[ll])

    def AddPolyKML(kml, llnw, llse, name, colour):
        """Adds a ploygon to a .kml file for display in Google Earth"""
        llne = [llse[0], llnw[1]]
        llsw = [llnw[0], llse[1]]
        pol = kml.newpolygon(name=name, outerboundaryis=[llnw, llne, llse, llsw])
        pol.style.polystyle.color = colour

    def PlotFile(fn, arr):
        """ saves the matrix as a .png image file. Used for debugging"""
        data = np.zeros((np.shape(arr)[0], np.shape(arr)[1], 3), dtype=np.uint8)  # height (num rows), width (num columns)
        for i in range(arr.shape[0]):  # rows
            for j in range(arr.shape[1]):  # cols
                if arr[i, j]:
                    data[i, j] = [255, 0, 0]
        img = Image.fromarray(data, 'RGB')
        img.save(fn + '.png')

    def Plot_xsecarea(ppos, pneg, pathpoint, level, direction, seq, innund):
        """"Plots an image of the cross sectional area of the Lahar at a particular point in a particular direction"""
        # Mostly usefule for debuggig but supports a bit more in depth analysis of a peculiar point on a lahar
        global draw1
        global font

        xsecarea = 0

        # plot from 2 cells to the 'positive' and two cells to the 'negative'
        if direction == "N-S":
            inc = Point([1, 0])
            dist = dem_cell_size
        elif direction == "W-E":
            inc = Point([0, 1])
            dist = dem_cell_size
        elif direction == "SW-NE":
            inc = Point([1, 1])
            dist = dem_cell_size * 2 ** 0.5
        elif direction == "NW-SE":
            inc = Point([-1, 1])
            dist = dem_cell_size * 2 ** 0.5

        pneg = pneg.minus(inc, "N")
        pneg = pneg.minus(inc, "N")
        ppos = ppos.plus(inc, "N")
        ppos = ppos.plus(inc, "N")

        # get number of cells
        rl = abs(ppos.vector()[0] - pneg.vector()[0]) + 1  # number of point along a row
        cl = abs(ppos.vector()[1] - pneg.vector()[1]) + 1  # number of points along a column
        ncells = max(rl, cl)

        # get bottom of channel
        chan_base = dem_v[pathpoint.vector()]
        pgborder = 50
        maxh = dem_v[pathpoint.vector()]
        minh = dem_v[pathpoint.vector()]

        p = pneg
        for i in range(ncells):
            if dem_v[p.vector()] > maxh:
                maxh = dem_v[p.vector()]
            if dem_v[p.vector()] < minh:
                minh = dem_v[p.vector()]
            p = p.plus(inc, "N")
        hrange = max(maxh - minh, level - minh)

        # set up image
        pheight = 1080
        pwidth = 1920
        pborder = 50
        pskyborder = 100
        img = Image.new('RGB', (pwidth, pheight), color='#000000')
        draw1 = ImageDraw.Draw(img, "RGBA")
        font = ImageFont.truetype("arial.ttf", 16)
        hh = (pheight - pborder * 2 - pgborder - pskyborder) / hrange  # height scaling factor
        ww = (pwidth - pborder * 2) / ncells  # width scaling factor

        p = pneg
        for i in range(ncells):
            # draw ground
            xsw = int(i * ww) + pborder
            xne = int((i + 1) * ww) - 1 + pborder
            ysw = pheight - pborder
            yne = pheight - (int((dem_v[p.vector()] - minh) * hh) + pgborder + pborder)
            draw1.rectangle([(xsw, ysw), (xne, yne)], fill='#548235')
            draw1.line([(xsw, ysw), (xsw, yne), (xne, yne), (xne, ysw), xsw, ysw], fill='#000000')

            PlotMsg("R:{} C:{}".format(p.vector()[0], p.vector()[1]), (xsw + xne) / 2, ysw + 1, "tc", "#FFFFFF")
            PlotMsg("Elev:{}".format(dem_v[p.vector()]), (xsw + xne) / 2, yne + 1, "tc", "#FFFFFF")

            # draw lahar
            if innund[p.vector()] and i in range(2, ncells - 2):
                xsecarea += (level - dem_v[p.vector()]) * dist
                xsw = int(i * ww) + pborder
                xne = int((i + 1) * ww) - 1 + pborder
                ysw = pheight - (int((dem_v[p.vector()] - minh) * hh) + pgborder + pborder)
                yne = pheight - (int((level - minh) * hh) + pgborder + pborder)
                draw1.rectangle([(xsw, ysw), (xne, yne)], fill='#8C3838')
                draw1.line([(xsw, ysw), (xsw, yne), (xne, yne), (xne, ysw), (xsw, ysw)], fill='#000000')
                if p == pathpoint:
                    PlotMsg("Level:{}".format(level), (xsw + xne) / 2, yne + 1, "tc", "#FFFFFF")

            # draw sky - assumes cordinates from either ground or lahar
            ysw = yne
            yne = pheight - (pheight - pborder)
            draw1.rectangle([(xsw, ysw), (xne, yne)], fill='#7DF5FB')
            draw1.line([(xsw, ysw), (xsw, yne), (xne, yne), (xne, ysw), (xsw, ysw)], fill='#000000')

            p = p.plus(inc, "N")

        PlotMsg("Cross Sectional Area Calculated: {:.2f} Cross Sectional Area Limit: {:.2f} Cell width: {:.2f}".format(xsecarea, xsec_area_limit, dist), pborder, pheight - (pheight - 10), "tl",
                "#FFFFFF")
        fn = "Point P{} R{}-C{}-{}".format(seq, pathpoint.vector()[0], pathpoint.vector()[1], direction)
        img.save(pxsecareafolder + "/" + fn + '.png')
        img.close

    def PlotMsg(msg, x, y, anchor="tl", fill="#000000"):
        """Plots text on the Cross Section Chart"""
        # anchor
        # t - top, m - middle, b - bottom
        # l = left, c = centre, r = right
        # assumes x,y origin of image in bottom left corner and the inversion to top left corner is handled elsewhere
        wt, ht = font.getsize(msg)
        if anchor[0] == 't':
            ht = 0
        elif anchor == "m":
            ht = ht / 2
        if anchor[1] == 'l':
            wt = 0
        elif anchor[1] == "c":
            wt = wt / 2
        draw1.text((x - wt, y - ht), msg, fill=fill, font=font)

    def ll2rc(ll):
        """converts lon and lat to row and column"""
        east, north = dem_crs(ll[0], ll[1])
        row, col = dem_f.index(east, north)  # spatial --> image coordinates
        return (row, col)

    def rc2ll(rc):
        """converts row and column to lon and lat"""
        # places at centre of cell - not se corner
        east, north = dem_f.xy(rc[0], rc[1])  # spatial --> image coordinates
        lon, lat = dem_crs(east, north, inverse=True)
        return (lon, lat)

    def lltransform(ll, dist, bearing):
        """returns new lon, lat of point [dist] away from [ll] at bearing [bearing]"""
        end_lon, end_lat, backaz = geod.fwd(ll[0], ll[1], bearing, dist)
        return (end_lon, end_lat)

    def rcdist(rc1, rc2):
        """returns the distance between two points based on row and column"""
        ll1 = rc2ll(rc1)
        ll2 = rc2ll(rc2)
        forward_az, backward_az, distance = geod.inv(ll1[0], ll1[1], ll2[0], ll2[1])
        return distance

    def PolygonDEM(kml, llnw, llse):
        """draw square on kml file for DEM scope"""
        AddPolyKML(kml, llnw, llse, "DEM", '4f00ff00')
        AddPointKML(kml, llnw, "DEM NW")
        AddPointKML(kml, llse, "DEM SE")

    def CreateSurfaceMesh():
        """Creates a mesh file of the DEM matrix surface"""
        log_msg("Preparing surface mesh domain...")
        a = sys.argv
        gmsh.initialize(sys.argv)
        gmsh.model.add("3DDEM")

        log_msg("Adding surface points...")
        p1 = []  # list of all points

        c_step = mesh_cols / pmeshrescol
        r_step = mesh_rows / pmeshresrow

        for i in range(pmeshrescol):  # cols
            for j in range(pmeshresrow):  # rows
                # Technically the point in the mesh is in the bottom left corner but with the elevation of the centre of the pixel. Probably.
                # As this is intended for visualisation of the landscape and energy cone, a uniform translation of half a pixel is probably not
                # that significant. Plus presented in paraview where it is in metres not lat/long
                x = (i * c_step + mesh_lc) * dem_cell_size
                y = ((pmeshresrow - 1 - j) * r_step + mesh_lr) * dem_cell_size  # reverse rows
                p1 += [gmsh.model.geo.addPoint(x, y, dem_v[int(j * r_step) + mesh_lr, int(i * c_step) + mesh_lc,])]  # todo assumes square pixels

        log_msg("Connecting Surface Lines...")
        hor_line = []  # list of all horizontal lines
        ver_line = []  # list of all vertical lines
        dia_line = []  # list of all diagonals

        for i in range(pmeshrescol):  # cols
            for j in range(pmeshresrow):  # rows
                base_index = i * pmeshresrow + j
                hplus_index = (i + 1) * pmeshresrow + j
                vplus_index = (i) * pmeshresrow + j + 1
                dplus_index = (i + 1) * pmeshresrow + j + 1

                if i < pmeshrescol - 1:
                    hor_line += [gmsh.model.geo.addLine(p1[base_index], p1[hplus_index]), ]
                if j < pmeshresrow - 1:
                    ver_line += [gmsh.model.geo.addLine(p1[base_index], p1[vplus_index]), ]
                if i < pmeshrescol - 1 and j < pmeshresrow - 1:
                    if p_diagonal == "SW-NE":
                        dia_line += [gmsh.model.geo.addLine(p1[base_index], p1[dplus_index]), ]
                    else:
                        dia_line += [gmsh.model.geo.addLine(p1[vplus_index], p1[hplus_index]), ]

        log_msg("Adding surface lines to loops...")
        curve_loop = []  # list of all curve loops
        for i in range(0, pmeshrescol - 1):
            for j in range(0, pmeshresrow - 1):
                h_index = i * pmeshresrow + j
                hplus_index = h_index + 1
                v_index = i * (pmeshresrow - 1) + j
                vplus_index = (i + 1) * (pmeshresrow - 1) + j
                d_index = i * (pmeshresrow - 1) + j
                if p_diagonal == "SW-NE":
                    curve_loop += [gmsh.model.geo.addCurveLoop([hor_line[h_index], ver_line[vplus_index], -dia_line[d_index]]), ]
                    curve_loop += [gmsh.model.geo.addCurveLoop([ver_line[v_index], hor_line[hplus_index], -dia_line[d_index]]), ]
                else:
                    curve_loop += [gmsh.model.geo.addCurveLoop([hor_line[h_index], -dia_line[d_index], -ver_line[v_index]]), ]
                    curve_loop += [gmsh.model.geo.addCurveLoop([hor_line[hplus_index], -ver_line[vplus_index], -dia_line[d_index]]), ]

        log_msg("Creating surface plane surfaces...")
        plane_surface = []  # list of all plane surfaces
        for i, j in enumerate(curve_loop):
            plane_surface += [gmsh.model.geo.addPlaneSurface([j]), ]

        # log_msg("Completing Surface Loop...")
        # gmsh.model.geo.removeAllDuplicates()
        # surface_loop = gmsh.model.geo.addSurfaceLoop(plane_surface)

        # log_msg("Creating Volume...")
        # vol = gmsh.model.geo.addVolume([surface_loop])

        log_msg("Generating surface mesh...")
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(3)

        log_msg("Saving surface mesh files...")

        # msh file for gmash
        gmsh.write("../" + pwdir + "/" + pmesh_dir + "/Surface.vtk")
        log_msg("../" + pwdir + "/" + pmesh_dir + "/Surface.vtk")
        gmsh.finalize()

    def CreateEnergyConeMesh():
        """Creates a mesh file of the energy cone"""
        log_msg("Preparing energy cone mesh domain...")
        a = sys.argv
        gmsh.initialize(sys.argv)
        gmsh.model.add("3DCone")

        log_msg("Adding cone points...")
        p1 = []  # list of all points

        c_step = mesh_cols / pmeshrescol
        r_step = mesh_rows / pmeshresrow

        px = peakrc[1] * dem_cell_size
        py = peakrc[0] * dem_cell_size

        for i in range(pmeshrescol):  # cols
            for j in range(pmeshresrow):  # rows
                # Technically the point in the mesh is in the bottom left corner but with the elevation of the centre of the pixel. Probably.
                # As this is intended for visualisation of the landscape and energy cone, a uniform translation of half a pixel is probably not
                # that significant. Plus presented in paraview where it is in metres not lat/long
                x = ((i * c_step) + mesh_lc) * dem_cell_size
                y = ((j * r_step) + mesh_lr) * dem_cell_size  # used for calculation
                r = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
                y = (((pmeshresrow - 1 - j) * r_step) + mesh_lr) * dem_cell_size  # reverse rows
                h = -r * phlratio + peak_height
                p1 += [gmsh.model.geo.addPoint(x, y, h, )]  # todo assumes square pixels with dem_cell_size; mesh resolution can be different in x and y

        log_msg("Connecting cone lines...")
        hor_line = []  # list of all horizontal lines
        ver_line = []  # list of all vertical lines
        dia_line = []  # list of all diagonals

        for i in range(pmeshrescol):  # cols
            for j in range(pmeshresrow):  # rows
                base_index = i * pmeshresrow + j
                hplus_index = (i + 1) * pmeshresrow + j
                vplus_index = (i) * pmeshresrow + j + 1
                dplus_index = (i + 1) * pmeshresrow + j + 1

                if i < pmeshrescol - 1:
                    hor_line += [gmsh.model.geo.addLine(p1[base_index], p1[hplus_index]), ]
                if j < pmeshresrow - 1:
                    ver_line += [gmsh.model.geo.addLine(p1[base_index], p1[vplus_index]), ]
                if i < pmeshrescol - 1 and j < pmeshresrow - 1:
                    if p_diagonal == "SW-NE":
                        dia_line += [gmsh.model.geo.addLine(p1[base_index], p1[dplus_index]), ]
                    else:
                        dia_line += [gmsh.model.geo.addLine(p1[vplus_index], p1[hplus_index]), ]

        log_msg("Adding cone lines to loops...")
        curve_loop = []  # list of all curve loops
        for i in range(0, pmeshrescol - 1):
            for j in range(0, pmeshresrow - 1):
                h_index = i * pmeshresrow + j
                hplus_index = h_index + 1
                v_index = i * (pmeshresrow - 1) + j
                vplus_index = (i + 1) * (pmeshresrow - 1) + j
                d_index = i * (pmeshresrow - 1) + j
                if p_diagonal == "SW-NE":
                    curve_loop += [gmsh.model.geo.addCurveLoop([hor_line[h_index], ver_line[vplus_index], -dia_line[d_index]]), ]
                    curve_loop += [gmsh.model.geo.addCurveLoop([ver_line[v_index], hor_line[hplus_index], -dia_line[d_index]]), ]
                else:
                    curve_loop += [gmsh.model.geo.addCurveLoop([hor_line[h_index], -dia_line[d_index], -ver_line[v_index]]), ]
                    curve_loop += [gmsh.model.geo.addCurveLoop([hor_line[hplus_index], -ver_line[vplus_index], -dia_line[d_index]]), ]

        log_msg("Creating cone plane surfaces...")
        plane_surface = []  # list of all plane surfaces
        for i, j in enumerate(curve_loop):
            plane_surface += [gmsh.model.geo.addPlaneSurface([j]), ]

        # log_msg("Completing Surface Loop...")
        # gmsh.model.geo.removeAllDuplicates()
        # surface_loop = gmsh.model.geo.addSurfaceLoop(plane_surface)

        # log_msg("Creating Volume...")
        # vol = gmsh.model.geo.addVolume([surface_loop])

        log_msg("Generating cone mesh...")
        gmsh.model.geo.synchronize()
        gmsh.model.mesh.generate(3)

        log_msg("Saving cone mesh files...")

        # msh file for gmash
        gmsh.write("../" + pwdir + "/" + pmesh_dir + "/Cone.vtk")
        gmsh.finalize()

    def GenLahar(v, ip):
        """Generates the lahar for a particular volume and initiation point"""
        global xsec_area_limit
        xsec_area_limit = 0.05 * v ** (2 / 3)  # Cross sectional area in m2
        plan_area_limit = 200 * v ** (2 / 3)  # Planimetric area in m2
        dy = 1  # Increment of elevation in m

        if pplotxsecarea and ip[0] == pplotip and v == pplotvol:
            xseccsv = csv.writer(open(pxsec_fn, "w"), delimiter=',', quoting=csv.QUOTE_ALL)
            xseccsv.writerow(["Point", "Latitude", "Longitude", "Row", "Col"])

        innund = np.zeros_like(dem_v)  # Defines a zeros rasters where the inundation cells will be writen as 1's values.
        plan_area = 0

        # cycle down the stream until the planometric area limit is exceeded
        # Stops when it reaches the sea
        ## Channel paths terminate 1 cell from the
        ## map edge so no danger of overflow.
        current_point = Point([ip[1], ip[2]])
        point_number = 1
        flow_direction = flowdir_v[current_point.vector()]  # 1 = NE, 2 = N, 3 = NW...continuing ACW until 8 = E. Some minus error values can exist on the edges

        while plan_area <= plan_area_limit and dem_v[current_point.vector()] > psealevel and flow_direction > 0:

            if flow_direction % 4 == 2:  # North or South ie 2 or 6
                ignore = "N-S"
            elif flow_direction % 4 == 0:  # East or West ie 4 or 8
                ignore = "W-E"
            elif flow_direction % 4 == 3:  # North West or South East ie 3 or 7
                ignore = "NW-SE"
            elif flow_direction % 4 == 1:  # North East or South West ie 1 or 5:
                ignore = "SW-NE"
            else:
                log_msg("Error: flow direction at point {} has value {} #1. Expecting values between 1-8. "
                      "Possibly this is because the point is at the very edge of the DEM. Terminating".format(current_point.vector(), flow_direction))
                sys.exit()

            if pplotxsecarea and ip[0] == pplotip and v == pplotvol:
                ipll = rc2ll((current_point.vector()[0], current_point.vector()[1]))
                xseccsv.writerow(["P{:02d}".format(point_number), ipll[1], ipll[0], current_point.vector()[0], current_point.vector()[1]])

            seq = str(point_number)
            plan_area, innund = EvalPoint(current_point, plan_area, plan_area_limit, v, ip, xsec_area_limit, innund, ignore, seq)

            # also evaluate adjacent point if flowing in a diagonal
            # if flowing NW, evaluate 1 point left (West)
            if flow_direction == 3 and dem_v[current_point.plus(Point([0, -1])).vector()] > psealevel:
                seq += "+W"
                plan_area, innund = EvalPoint(current_point.plus(Point([0, -1])), plan_area, plan_area_limit, v, ip, xsec_area_limit, innund, ignore, seq)
                if pplotxsecarea and ip[0] == pplotip and v == pplotvol:
                    ipll = rc2ll((current_point.plus(Point([0, -1])).vector()))
                    xseccsv.writerow(["P{:02d}W".format(point_number), ipll[1], ipll[0], current_point.plus(Point([0, -1])).vector()[0], current_point.plus(Point([0, -1])).vector()[1]])
            # if flowing SW, evaluate 1 point below (South) - note that the DEM is inverted hence the vector for south is 1,0 rather than -1,0
            elif flow_direction == 5 and dem_v[current_point.plus(Point([1, 0])).vector()] > psealevel:
                seq += "+S"
                plan_area, innund = EvalPoint(current_point.plus(Point([1, 0])), plan_area, plan_area_limit, v, ip, xsec_area_limit, innund, ignore, seq)
                if pplotxsecarea and ip[0] == pplotip and v == pplotvol:
                    ipll = rc2ll((current_point.plus(Point([1, 0])).vector()))
                    xseccsv.writerow(["P{:02d}S".format(point_number), ipll[1], ipll[0], current_point.plus(Point([1, 0])).vector()[0], current_point.plus(Point([1, 0])).vector()[1]])

            # if flowing SE, evaluate 1 point left (East)
            elif flow_direction == 7 and dem_v[current_point.plus(Point([0, 1])).vector()] > psealevel:
                seq += "+E"
                plan_area, innund = EvalPoint(current_point.plus(Point([0, 1])), plan_area, plan_area_limit, v, ip, xsec_area_limit, innund, ignore, seq)
                if pplotxsecarea and ip[0] == pplotip and v == pplotvol:
                    ipll = rc2ll((current_point.plus(Point([0, 1])).vector()))
                    xseccsv.writerow(["P{:02d}E".format(point_number), ipll[1], ipll[0], current_point.plus(Point([0, 1])).vector()[0], current_point.plus(Point([0, 1])).vector()[1]])

            # if flowing NE, evaluate 1 point up (North)
            elif flow_direction == 1 and dem_v[current_point.plus(Point([-1, 0])).vector()] > psealevel:
                plan_area, innund = EvalPoint(current_point.plus(Point([-1, 0])), plan_area, plan_area_limit, v, ip, xsec_area_limit, innund, ignore, seq)
                seq += "+N"
                if pplotxsecarea and ip[0] == pplotip and v == pplotvol:
                    ipll = rc2ll((current_point.plus(Point([-1, 0])).vector()))
                    xseccsv.writerow(["P{:02d}N".format(point_number), ipll[1], ipll[0], current_point.plus(Point([-1, 0])).vector()[0], current_point.plus(Point([-1, 0])).vector()[1]])

            # next point
            if flow_direction == 1:
                current_point = current_point.plus(Point([-1, 1]))
            elif flow_direction == 2:
                current_point = current_point.plus(Point([-1, 0]))
            elif flow_direction == 3:
                current_point = current_point.plus(Point([-1, -1]))
            elif flow_direction == 4:
                current_point = current_point.plus(Point([0, -1]))
            elif flow_direction == 5:
                current_point = current_point.plus(Point([1, -1]))
            elif flow_direction == 6:
                current_point = current_point.plus(Point([1, 0]))
            elif flow_direction == 7:
                current_point = current_point.plus(Point([1, 1]))
            elif flow_direction == 8:
                current_point = current_point.plus(Point([0, 1]))
            else:
                log_msg("Error: flow direction at point {} has value {} #2. Expecting values between 1-8. "
                      "Possibly this is because the point is at the very edge of the DEM. Terminating".format(current_point.vector(), flow_direction))
                sys.exit()
            flow_direction = flowdir_v[current_point.vector()]  # 1 = NE, 2 = N, 3 = NW...continuing ACW until 8 = E. Some minus error values can exist on the edges
            point_number += 1
        if flow_direction <= 0:
            log_msg("Warning: flow direction at point {} has value {} #2. Expecting values between 1-8. "
                  "This is because the lahar has reached the very edge of the DEM.".format(current_point.vector(), flow_direction))

        return innund

    def EvalPoint(pathpoint, plan_area, plan_area_limit, v, ip, xsec_area_limit, innund, ignore, seq):
        """Evaluates a point on the lahar"""
        # increments the lahar level from the elevation of the channel point being considered until the cross sectional area
        # limit is met. Does this four times - ie in each of the following directions: N-S, E-W, NW-SE and SW-NE. Cross
        # sectional area is the sum of the area in all four directions.
        innund[pathpoint.vector()] = 1
        directions = ["N-S", "W-E", "NW-SE", "SW-NE"]

        for i in directions:
            # cycle through each direction. Sets a vector to move in a positive direction and a negative direction away from the
            # initial point. Positive and negative are arbitrary terms to describe the opposite directions. If direction is
            # diagonal then each step has a distance of root 2.
            # Cross sectional areas where the profile is in the direction of the stream are ignored
            #
            # If the calculation of the cross sectional area over tops a local maximum, the area of the downstream section is
            # not considered. This doesn't seem to be a case considered in Schilling
            #
            # The class Point is used as the plus and minus operators prevent overflow if the cross sectional area is close to
            # the boundary. In this case the positive or negitive point remains on the boundary as the level increases.
            # To be technically correct, a larger DEM should be used to allow the cross sectional area and innundation to
            # be completed. A warning is printed in the Plus or Minus operations in the class.

            if i != ignore:
                if i == "N-S":
                    pos_vect = Point([1, 0])
                    neg_vect = Point([-1, 0])
                    inc_dist = dem_cell_size
                elif i == "W-E":
                    pos_vect = Point([0, 1])
                    neg_vect = Point([0, -1])
                    inc_dist = dem_cell_size
                elif i == "NW-SE":
                    pos_vect = Point([-1, 1])
                    neg_vect = Point([1, -1])
                    inc_dist = 2 ** 0.5 * dem_cell_size
                elif i == "SW-NE":
                    pos_vect = Point([1, 1])
                    neg_vect = Point([-1, -1])
                    inc_dist = 2 ** 0.5 * dem_cell_size

                dy = 1
                dist = inc_dist
                xsec_area = inc_dist + dy
                level = dem_v[pathpoint.vector()] + dy  # initial level of flow
                p_pos = pathpoint  # set both points to the initial path point
                p_neg = pathpoint  # set both points to the initial path point

                while xsec_area <= xsec_area_limit and plan_area <= plan_area_limit:
                    raise_level = True
                    p_pos_new = p_pos.plus(pos_vect)
                    p_pos_new_level = dem_v[p_pos_new.vector()]
                    if level > p_pos_new_level and p_pos_new_level > psealevel:
                        p_pos = p_pos_new
                        dist += inc_dist
                        xsec_area += inc_dist * (level - dem_v[p_pos.vector()])
                        innund[p_pos.vector()] = 1
                        plan_area += dem_cell_size ** 2
                        raise_level = False

                    if xsec_area <= xsec_area_limit:
                        p_neg_new = p_neg.plus(neg_vect)
                        p_neg_new_level = dem_v[p_neg_new.vector()]
                        if level > p_neg_new_level and p_neg_new_level > psealevel:
                            p_neg = p_neg_new
                            dist += inc_dist
                            xsec_area += inc_dist * (level - dem_v[p_neg.vector()])
                            innund[p_neg.vector()] = 1
                            plan_area += dem_cell_size ** 2
                            raise_level = False

                    if raise_level and xsec_area <= xsec_area_limit:
                        level += dy
                        xsec_area += dist * dy

                if pplotxsecarea and ip[0] == pplotip and v == pplotvol:
                    Plot_xsecarea(p_pos, p_neg, pathpoint, level, i, seq, innund)

        return (plan_area, innund)

    def op_ec_points(ec_points):
        """Dumps out all points on the energy cone line for debugging"""
        ec_fn = "../{}/{}".format(pwdir, "ec_points.csv")
        epcsv = csv.writer(open(ec_fn, "w"), delimiter=',', dialect="excel", quoting=csv.QUOTE_MINIMAL)
        epcsv.writerow(["Label", "Latitude", "Longitude", "Row", "Column"])
        for i, irc in enumerate(ec_points):
            ll = rc2ll(irc)
            epcsv.writerow(["P"+str(i), ll[1], ll[0], irc[0], irc[1]])

    #Start of Lahar sub routine
    pwdir = app.pwdir
    pdem_fn = app.pdem_fn
    pthal_fn = app.pthal_fn
    pflow_fn = app.pflow_fn
    pvolume = app.pvolume
    phlratio = app.phlratio
    # ppeak_entry = app.ppeak_entry.reverse() #revert back to long, lat order
    ppeak_entry = list(reversed(app.ppeak_entry)) #revert back to long, lat order
    phprange = app.phprange/2 #Program uses half diagonals
    psealevel = app.psealevel
    plahar_dir = app.plahar_dir
    pinitpoints_fn = app.pinitpoints_fn
    plog_fn = app.plog_fn
    pecraw_fn = app.pecraw_fn
    pecfilled_fn = app.pecfilled_fn
    pecline_fn = app.pecline_fn
    pplotmesh = app.pplotmesh
    pmesh_dir = app.pmesh_dir
    pmeshres = app.pmeshres
    pmeshsize = app.pmeshsize
    pcalcinitpoints = app.pcalcinitpoints
    puserowcol = app.puserowcol
    piponly = app.piponly

    pinitpoints_fn = "../{}/{}".format(pwdir, pinitpoints_fn)
    plog_fn = "../{}/{}".format(pwdir, plog_fn)

    ptextcrs = "EPSG:4326"
    pwritetif = True  # write output as tif files
    pwriteascii = False  # write output as ascii files
    pwritecsv = False  # write output as csv files

    # Cross Sectional Area Parameters - parameters do not come from screen entry - code only - for debugging
    pplotxsecarea = False  # draw plots of cross sectional areas
    pxsecareafolder = ("XSecArea")  # folder to store plots in. If it doesnt exist create it as PIL doesn't create folder
    pxsecareafolder = "../{}/{}".format(pwdir, pxsecareafolder)
    pplotip = 13  # which initiation point to draw the plots for
    pplotvol = 1e4  # which volume to draw the plots for
    pxsec_fn = "Cross Section Points.csv"
    pxsec_fn = "{}/{}".format(pxsecareafolder, pxsec_fn)

    # Additonal Mesh Parameters
    p_diagonal = "SW-NE"  # which direction the diaginal is drawn on the mesh. Any other value is SE-NW
    pmeshrescol = pmeshres #uses the same resolution for both directions from the screen parameter
    pmeshresrow = pmeshres

    log_msg("LaharZ Starting", initfile = True)
    log_msg("Parameters", screen_op = False)
    log_msg('Parameter: pwdir; Working directory; Value: ' + pwdir, screen_op = False)
    log_msg('Parameter: pdem_fn; DEM file; Value: ' + pdem_fn, screen_op = False)
    log_msg('Parameter: pthal_fn; Stream (or thalweg) file; Value: ' + pthal_fn, screen_op = False)
    log_msg('Parameter: pflow_fn; Flow file; Value: ' + pflow_fn, screen_op = False)
    log_msg('Parameter: pvolume; Volumes; Value: ' + str(pvolume), screen_op = False)
    log_msg('Parameter: phlratio; H/H Ratio; Value: ' + str(phlratio), screen_op = False)
    log_msg('Parameter: ppeak_entry; Entered values for peak; Value: ' + str(list(reversed(ppeak_entry))), screen_op = False) # in lat long order to match input
    log_msg('Parameter: phprange; Range to search; Value: ' + str(phprange*2), screen_op = False) #x2 to match input. Program uses half diagonals
    log_msg('Parameter: psealevel; Sea level; Value: ' + str(psealevel), screen_op = False)
    log_msg('Parameter: plahar_dir; Lahar Directory; Value: ' + plahar_dir, screen_op = False)
    log_msg('Parameter: pinitpoints_fn; Inititation Points; Value: ' + pinitpoints_fn, screen_op = False)
    log_msg('Parameter: plog_fn; Log file; Value: ' + plog_fn, screen_op = False)
    log_msg('Parameter: pecraw_fn; Energy Cone (Raw) file; Value: ' + pecraw_fn, screen_op = False)
    log_msg('Parameter: pecfilled_fn; Energy Cone (Filled) file; Value: ' + pecfilled_fn, screen_op = False)
    log_msg('Parameter: pecline_fn; Energy Cone (Line) file; Value: ' + pecline_fn, screen_op = False)
    log_msg('Parameter: pplotmesh; Flag to plot mesh; Value: ' + str(pplotmesh), screen_op = False)
    log_msg('Parameter: pmesh_dir; Mesh directory; Value: ' + pmesh_dir, screen_op = False)
    log_msg('Parameter: pmeshres; Mesh resolution; Value: ' + str(pmeshres), screen_op = False)
    log_msg('Parameter: pmeshsize; Mesh Extent; Value: ' + str(pmeshsize), screen_op = False)
    log_msg('Parameter: pcalcinitpoints; Calculate or Load initiation points; Value: ' + pcalcinitpoints, screen_op = False)
    log_msg('Parameter: puserowcol; Use row and columns (otherwise Latitude and longitude) from loaded initiation points; Value: ' + str(puserowcol), screen_op = False)
    log_msg('Parameter: piponly; Flag to calculate initiation points only; Value: ' + str(piponly), screen_op = False)
    log_msg('Parameter: pinitpoints_fn; Initiation points file name; Value: ' + pinitpoints_fn, screen_op = False)
    log_msg('Parameter: ptextcrs; Coordinate Reference System to use for Ascii (Text) files; Value: ' + ptextcrs, screen_op = False)
    log_msg('Parameter: pwritetif; Flag to write outputs in tif files; Value: ' + str(pwritetif), screen_op = False)
    log_msg('Parameter: pwriteascii; Flag to write outputs in Ascii (Text); Value: ' + str(pwriteascii), screen_op = False)
    log_msg('Parameter: pwritecsv; Flag to write outputs in csv; Value: ' + str(pwritecsv), screen_op = False)
    log_msg('Parameter: pplotxsecarea; Flag to plot Cross Sectional Areas; Value: ' + str(pplotxsecarea), screen_op=False)
    log_msg('Parameter: pxsecareafolder; Folder for cross sectional areas; Value: ' + pxsecareafolder, screen_op=False)
    log_msg('Parameter: pplotip; Initial point to plot cross sectional areas for; Value: ' + str(pplotip), screen_op=False)
    log_msg('Parameter: pplotvol; Volume to plot cross sectional areas for; Value: ' + str(pplotvol), screen_op=False)
    log_msg('Parameter: pxsec_fn; CSV file of all points in a lahar where the cross sectional area has been plotted; Value: ' + pxsec_fn, screen_op=False)
    log_msg('Parameter: p_diagonal; Diagonal to use on mesh; Value: ' + p_diagonal, screen_op=False)
    log_msg('Parameter: pmeshrescol; Mesh resolution (columns); Value: ' + str(pmeshrescol), screen_op=False)
    log_msg('Parameter: pmeshresrow; Mesh resolution (rows); Value: ' + str(pmeshresrow), screen_op=False)

    if not piponly:
        chk_folder = os.path.isdir("../{}/{}".format(pwdir, plahar_dir))
        # If folder doesn't exist, then create it.
        if not chk_folder:
            os.makedirs("../{}/{}".format(pwdir, plahar_dir))

    if pplotxsecarea:
        chk_folder = os.path.isdir("../{}/{}".format(pwdir, pxsecareafolder))
        # If folder doesn't exist, then create it.
        if not chk_folder:
            os.makedirs("../{}/{}".format(pwdir, pxsecareafolder))

    if pplotmesh:
        chk_folder = os.path.isdir("../{}/{}".format(pwdir, pmesh_dir))
        # If folder doesn't exist, then create it.
        if not chk_folder:
            os.makedirs("../{}/{}".format(pwdir, pmesh_dir))

    # Initialisations ##########################################################################################################
    log_msg("Initialisations...")
    kml = simplekml.Kml()
    geod = pyproj.Geod(ellps='WGS84')  # used as the projection method to determine distances between two points

    # Load DEM #################################################################################################################
    log_msg("Loading DEM...")
    dem_f, dem_crs, dem_v = LoadFile(pdem_fn)

    # todo 1) find a method of determing the cell size from the input file. Using the transform method is different depending on the
    # projection method. It will return meters or degrees. Currently the cell distance is just calculated from the distance between
    # two cells. This results in a slightly different value than using the transform method
    # todo 2) currently assumes cells in the matrix are square. This may not be appropriate for some project methods/tif files

    # dem_cell_size = dem_f.transform[0]
    dem_cell_size = rcdist((0, 0), (0, 1))  # distance in x direction, ie one column

    nrows = dem_v.shape[0]
    ncols = dem_v.shape[1]

    dem_se_ll = rc2ll((nrows - 1, ncols - 1))
    dem_nw_ll = rc2ll((0, 0))
    PolygonDEM(kml, dem_nw_ll, dem_se_ll)  # creates a polygon (rectangle) of the DEM area for reading in google maps

    # Load Flow Direction file
    log_msg("Loading Flow Direction file...")
    flowdir_f, flowdir_crs, flowdir_v = LoadFile(pflow_fn)
    if flowdir_v.shape != dem_v.shape or dem_crs != flowdir_crs:
        log_msg("Error - mismatch in raster size and projection between DEM file ({}) and Flow Direction file ({})".format(pdem_fn, pflow_fn), errmsg = True)
        return

    if pcalcinitpoints == 'calc':
        log_msg("Loading Stream file...")
        thal_f, thal_crs, thal_v = LoadFile(pthal_fn)
        if thal_v.shape != dem_v.shape or dem_crs != thal_crs:
            log_msg("Error - mismatch in raster size and projection between DEM file ({}) and Stream file ({})".format(pdem_fn, pthal_fn), errmsg = True)
            return

        thal_v[thal_v == 65535] = 0  # set all 'NaN' values of #FFFF to zero #todo this is necessary for some outputs from GRASS r.fillnull
        thal_v[thal_v < 0] = 0  # set all negatives to zero
        thal_v[thal_v > 0] = 1  # set all stream numbers to 1

        # Find peak
        # Adds peak and the search box to the kml file for display in google earth
        log_msg("Determining High Point...")
        AddPointKML(kml, ppeak_entry, "Entry Point")
        search_nw_ll = lltransform(ppeak_entry, phprange, 315)  # nw corner of search box
        AddPointKML(kml, search_nw_ll, "Search NW")
        search_se_ll = lltransform(ppeak_entry, phprange, 135)  # se corner of search box
        AddPointKML(kml, search_se_ll, "Search SE")
        AddPolyKML(kml, search_nw_ll, search_se_ll, "Search Area", "4f0000ff")

        search_nw_rc = ll2rc(search_nw_ll)
        search_se_rc = ll2rc(search_se_ll)
        if not (0 <= search_nw_rc[0] < nrows and 0 <= search_nw_rc[1] <= ncols and 0 <= search_se_rc[0] < nrows and 0 <= search_se_rc[1] <= ncols):
            log_msg("Error: Search area for high point is not wholly within the DEM file", errmsg = True)
            return

        search_area = dem_v[search_nw_rc[0]:search_se_rc[0] + 1, search_nw_rc[1]:search_se_rc[1] + 1]  # area to search for highest point
        peak_height = np.amax(search_area)  # height of highest point
        sarearc = np.where(search_area == peak_height)  # row and column of highest point in search box
        peakrc = np.zeros(2).astype(int)
        peakrc[0] = sarearc[0][0] + search_nw_rc[0]  # row and column in overall table
        peakrc[1] = sarearc[1][0] + search_nw_rc[1]

        peakll = rc2ll(peakrc)
        AddPointKML(kml, peakll, "High Point")
        kml.save("KMLFile.kml")

        # Determine Energy Cone
        log_msg("Generating Energy Cone...")

        ###############################################################################################################################################
        ###############################################################################################################################################

        b = np.indices((nrows, ncols), float)
        print("Ignore the warning messages relating to division by zero")
        #todo suppress warning messages for div/zero
        ecraw_v = (peak_height - dem_v) / ((((b[0] - peakrc[0]) ** 2) + ((b[1] - peakrc[1]) ** 2)) ** .5 * dem_cell_size)
        ecraw_v[peakrc[0], peakrc[1]] = 9999
        ecraw_v = ecraw_v > phlratio

        SaveFile(pecraw_fn, dem_f, ecraw_v)

        log_msg("Filling Energy Cone...")
        ecfilled_v = binary_fill_holes(ecraw_v)
        SaveFile(pecfilled_fn, dem_f, ecfilled_v)

        log_msg("Generating Energy Cone Line...")
        ecline_v = binary_erosion(input=ecfilled_v)
        ecline_v = np.logical_and(ecraw_v, np.logical_not(ecline_v))
        SaveFile(pecline_fn, dem_f, ecline_v)

        # inititiation points
        log_msg("Generating Initiation Points...")
        ec_points = np.argwhere(ecline_v == 1)
        op_ec_points(ec_points) #creates csv file of ec_points for debugging
        initrc = []
        ip_counter = 1
        for ii, i in enumerate(ec_points): #to allow breakpoints to be set at specific points for debugging
            # checks if the ec line and the thalweg share the same cell in the matix: if so, they cross and hence an initiation point
            # but also checks if the lines cross in an x where they don;t share the same cell. This is done in each direction.
            if thal_v[tuple(i)] == 1:
                initrc.append([ip_counter, i[0], i[1]])
                ip_counter += 1
            else:
                # a b c
                # d e f
                # g h j
                # nw direction
                ip_found = False
                if i[0] < nrows and i[1] < ncols:
                    b = [i[0] + 1, i[1]]
                    c = [i[0] + 1, i[1] + 1]
                    f = [i[0], i[1] + 1]
                    if (ecline_v[tuple(b)] == 0 and thal_v[tuple(b)] == 1 and
                            ecline_v[tuple(c)] == 1 and thal_v[tuple(c)] == 0 and
                            ecline_v[tuple(f)] == 0 and thal_v[tuple(f)] == 1):
                        initrc.append([ip_counter, b[0], b[1]])
                        log_msg("Adding extra ip: " + str(ip_counter))
                        ip_counter += 1
                        ip_found = True
                # se direction
                if i[0] > 0 and i[1] < ncols and not ip_found:
                    f = [i[0], i[1] + 1]
                    h = [i[0] - 1, i[1]]
                    j = [i[0] - 1, i[1] + 1]
                    if (ecline_v[tuple(f)] == 0 and thal_v[tuple(f)] == 1 and
                            ecline_v[tuple(h)] == 0 and thal_v[tuple(h)] == 1 and
                            ecline_v[tuple(j)] == 1 and thal_v[tuple(j)] == 0):
                        initrc.append([ip_counter, f[0], f[1]])
                        log_msg("Adding extra ip: " + str(ip_counter))
                        ip_counter += 1
                        ip_found = True
                # # sw direction
                # if i[0] > 0 and i[1] > 0 and not ip_found:
                #     d = [i[0], i[1] - 1]
                #     g = [i[0] - 1, i[1] - 1]
                #     h = [i[0] - 1, i[1]]
                #     if (ecline_v[tuple(d)] == 0 and thal_v[tuple(d)] == 1 and
                #             ecline_v[tuple(g)] == 1 and thal_v[tuple(g)] == 0 and
                #             ecline_v[tuple(i)] == 0 and thal_v[tuple(h)] == 1):
                #         initrc.append([ip_counter, d[0], d[1]])
                #         log_msg("Adding extra ip: " + str(ip_counter))
                #         ip_counter += 1
                #         ip_found =  True
                # # ne direction
                # if i[0] < nrows and i[1] > 0 and not ip_found:
                #     a = [i[0] + 1, i[1] - 1]
                #     b = [i[0] + 1, i[1]]
                #     d = [i[0], i[1] - 1]
                #     if (ecline_v[tuple(a)] == 1 and thal_v[tuple(a)] == 0 and
                #             ecline_v[tuple(b)] == 0 and thal_v[tuple(b)] == 1 and
                #             ecline_v[tuple(d)] == 0 and thal_v[tuple(d)] == 1):
                #         initrc.append([ip_counter, b[0], b[1]])
                #         log_msg("Adding extra ip: " + str(ip_counter))
                #         ip_counter += 1
                #         ip_found = True

        initrc = np.array(initrc)

        # Initiation points and peak saved in a csv file. This can be edited and reloaded

        ipcsv = csv.writer(open(pinitpoints_fn, "w"), delimiter=',', dialect="excel", quoting=csv.QUOTE_MINIMAL)
        ipcsv.writerow(["Label", "Latitude", "Longitude", "Number", "Row", "Column"])
        ipcsv.writerow(["Peak", peakll[1], peakll[0], "", peakrc[0], peakrc[1]])

        for i, irc in enumerate(initrc):
            ll = rc2ll(irc[1:3])  # this programme uses long, lat to match x,y directions. Presented as Lat, Long in all output
            ipcsv.writerow(["IP{:02d}".format(irc[0]), ll[1], ll[0], irc[0], irc[1], irc[2]])

        if pplotmesh:
            # determine the parameters to use for the size of the mesh files
            maxr = np.amax(initrc[:, 1])
            minr = np.amin(initrc[:, 1])
            centr = int((maxr + minr) / 2)
            maxc = np.amax(initrc[:, 2])
            minc = np.amin(initrc[:, 2])
            centc = int((maxc + minc) / 2)

            mesh_ur = int(min(centr + (maxr - centr) * pmeshsize, nrows - 1))
            mesh_lr = int(max(centr - (centr - minr) * pmeshsize, 0))
            mesh_uc = int(min(centc + (maxc - centc) * pmeshsize, ncols - 1))
            mesh_lc = int(max(centc - (centc - minc) * pmeshsize, 0))

            mesh_rows = mesh_ur - mesh_lr + 1
            mesh_cols = mesh_uc - mesh_lc + 1

            CreateSurfaceMesh()
            CreateEnergyConeMesh()

    else:
        # load in initiation points from file. This is intended for quicker execution when the same scenario is
        # rerun. There are no checks to see if the initiation points from the file were originally generated using the
        # same DEM and Flow files. Nor are there are checks to ensure that the values read in are within the
        # DEM and Accumulation files - ie these files could be edited to reflect points outside the DEM and Accumulation
        # files; this will result in errors.

        log_msg("Loading Initiation Points...")
        ipload = np.loadtxt(pinitpoints_fn, delimiter=',', dtype="float", skiprows=2, usecols=np.arange(1, 6))
        if ipload.ndim == 1: # a single line is enumerated by element rather than by line
            ipload = np.reshape(ipload, (1, ipload.size))
        initrc = np.empty([0, 3], dtype="int")
        for i, line in enumerate(ipload):
            if puserowcol:
                r_in, c_in = line[3:5]
            else:
                # file is sequenced latitude and longitude for presentation consistency. The programme uses
                # longitude and latitude to align to x,y axis. Hence the order read in needs to be reversed.
                r_in, c_in = ll2rc([line[1], line[0]])
            if 0 <= r_in < nrows and 0 <= c_in < ncols:
                initrc = np.append(initrc, [[line[2], r_in, c_in]], axis=0)
            else:
                log_msg("Warning: Point {} ignored as it is outside the DEM file".format(line[2]))
        initrc = initrc.astype('int') #reverting to integer as append converts to float64

    if not piponly:  # if not calculate initiation points only
        if len(initrc)> 0:

            # Calculate Lahars
            log_msg("Generating Lahars...")
            innund_total_v = np.zeros_like(dem_v)  # array for total innundations
            for v1, v in enumerate(pvolume):
                innund_vol_v = np.zeros_like(dem_v)  # array for all innundations for a particular volume

                for i, ip in enumerate(initrc):
                    log_msg("Generating Lahar. Initiation Point: {} {}/{} Volume: {:.2e} {}/{} ".format(ip[0], i + 1, initrc.shape[0], v, v1 + 1, len(pvolume)))
                    innund_v = GenLahar(v, ip)

                    ofn = "{}/IP{:02d}-V{:.2e}".format(plahar_dir, ip[0], v).replace("+", "").replace(".", "-")
                    ll = rc2ll(ip[1:3])
                    log_msg("IP{:02d} Latitude: {} Longitude: {} Row: {} Column: {} Volume: {} Filename: {}".format(ip[0], ll[1], ll[0], ip[1], ip[2], v, ofn), screen_op=False)  # todo file extension?

                    log_msg("Writing : {}...".format(ofn), screen_op=False)
                    SaveFile(ofn, dem_f, innund_v)
                    innund_vol_v = np.where(innund_vol_v == 0, innund_v * ip[0], innund_vol_v)  # add innundation for one initiation point and volume to the overall volume array

                # save overall volume file
                ofn = "{}/V{:.2e}".format(plahar_dir, v).replace("+", "").replace(".", "-")
                log_msg("Writing : {}...".format(ofn))
                SaveFile(ofn, dem_f, innund_vol_v)
                innund_total_v = np.where(innund_total_v == 0, (innund_vol_v > 0) * (v1 + 1), innund_total_v)  # add volume innundation to the total innundation

            # save total innundation array
            ofn = "{}/Total".format(plahar_dir)
            log_msg("Writing : {}...".format(ofn))
            SaveFile(ofn, dem_f, innund_total_v)
            log_msg("Finished")
        else:
            log_msg("No valid initiation points")
    else:
        log_msg("Finished")

# Main
if os.environ.get('DISPLAY','') == '':
    #print('no display found. Using :0.0')
    os.environ.__setitem__('DISPLAY', ':0.0')

#create main window
param1 = tk.Tk()
param1.title("LaharZ")
param1.geometry("1920x1080")

#create a frame
app = Application(param1)
app.pack(side="top", fill="both", expand=True)

# Run forever!
param1.mainloop()
