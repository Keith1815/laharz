# Version 2.0.0 Released: Oct 2023
# Development version#

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
#Laharz v1.0.2 - replaced gmsh with trimesh to allow packaging on conda forge. Minor fixes
#Laharz v1.0.3 - corrected mesh cone projection, extraneous new lines in xl csv output and errors in determining initiation points close to the edge
#Laharz v1.0.4 - initiation points as editable geopackage, able to edit in QGIS

#Laharz v2.0.0 - Major rewrite. New GUI. Ability to select apex for energy cone. Editable initiation points. Incrementatal heght on energy cone apex.

#==================================================================================================================================================================================
__version__ = "2.0.0"
import tkinter as tk
import os
from pathlib import Path
from tkinter import ttk as ttk
import pickle
from shapely.geometry import Polygon
from shapely.geometry import Point as shPoint
import geopandas as gpd
import pyproj as pj
import datetime
from statistics import mean
import numpy as np
import rasterio as rio
from rasterio.rio.helpers import resolve_inout
import sys
from scipy.ndimage import binary_erosion, binary_fill_holes
import csv
from PIL import Image, ImageDraw, ImageFont, ImageTk
from importlib.resources import files, as_file

class LaharZ_app(tk.Tk): 
    def __init__(self):
        super().__init__() #copies attributes from parent class (tk)
        self.geometry('1920x1080')
        self.title('LaharZ')
        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)

        # # set up frame (us tk not tkk)
        m_frame = tk.Frame(self, width = 1980, heigh = 1080)

        m_frame.columnconfigure(0, weight = 1)
        m_frame.rowconfigure(0, weight = 1)
        m_frame.grid(row = 0, column = 0, sticky=tk.NSEW)
               
        # Add a canvas in that frame.
        self.canvas = tk.Canvas(m_frame) #, width = 1980, height = 1080)
        self.canvas.grid(row = 0, column = 0, padx = 10, pady = 10, sticky=tk.NSEW)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.canvas.columnconfigure(0, weight = 1)
        self.canvas.rowconfigure(0, weight = 1)
        
        # # Create a vertical scrollbar linked to the canvas.
        vsbar = tk.Scrollbar(self.canvas, orient=tk.VERTICAL, command=self.canvas.yview)
        vsbar.grid(row=0, column = 1, sticky=tk.NS)
        self.canvas.configure(yscrollcommand=vsbar.set)

        self.sts_msg = "Welcome to LaharZ"
        self.sts_msg2 = "Activities will be logged in " + log_fn
        self.exec_frame0() #splash
        self.exec_frame1() #populate widgets

    def exec_frame0(self):
        # Create a frame on the canvas to contain the widgets
        f1 = tk.Frame(self.canvas, width = 600, height = 346)
        f1.columnconfigure(0, weight = 1)
        f1.rowconfigure(0, weight = 1)
        f1.grid(row = 0, column = 0, sticky = "")

        c2 = tk.Canvas(f1, width = 600, height = 173)
        c2.columnconfigure(0, weight = 1)
        c2.rowconfigure(0, weight = 1)
        c2.grid(row = 2, column = 0, sticky = "")

        tk.Label(f1, text='LaharZ', font=('Times New Roman', 120, 'italic')).grid(row=0, column = 0, columnspan=1, sticky='')
        tk.Label(f1, text='', font=('Times New Roman', 10, 'italic')).grid(row=1, column = 0, columnspan=1, sticky='')
        # tk.Label(f1, text='Version: ' + __version__, font=('Times New Roman', 20)).grid(row=4, column = 0, columnspan=1, sticky='W')
        # tk.Label(f1, text='', font=('Times New Roman', 20)).grid(row=3, column = 0, columnspan=1, sticky='W')

        if 'site-packages' in __file__:
            logo_source = files('laharz').joinpath('uob.png')
            with as_file(logo_source) as logo_f:
                with Image.open(logo_f) as image:
                    c2.image = ImageTk.PhotoImage(image)
                    c2.create_image(0, 0, image=c2.image, anchor='nw')
            tk.Label(f1, text='Version: ' + __version__ + ' package', font=('Times New Roman', 20)).grid(row=4, column = 0, columnspan=1, sticky='W')
            tk.Label(f1, text='', font=('Times New Roman', 20)).grid(row=3, column = 0, columnspan=1, sticky='W')
        else:
            try:
                c2.image = ImageTk.PhotoImage(Image.open('uob.png'))
                c2.create_image(0, 0, image=c2.image, anchor='nw')
                tk.Label(f1, text='Version: ' + __version__ + ' stand alone', font=('Times New Roman', 20)).grid(row=4, column = 0, columnspan=1, sticky='W')
                tk.Label(f1, text='', font=('Times New Roman', 20)).grid(row=3, column = 0, columnspan=1, sticky='W')
            except:
                tk.Label(f1, text='Version: ' + __version__ + ' stand alone, no logo', font=('Times New Roman', 20)).grid(row=4, column = 0, columnspan=1, sticky='W')
                tk.Label(f1, text='', font=('Times New Roman', 20)).grid(row=3, column = 0, columnspan=1, sticky='W')


        self.canvas.update()
        f1.after(3000, f1.destroy())

    def exec_frame1(self):

        def create_frame():
            # Create a frame on the canvas to contain the widgets
            frame = tk.Frame(self.canvas)
            frame.columnconfigure(0, weight = 1)
            frame.rowconfigure(0, weight = 1)
            frame.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = tk.NW)
            frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            self.canvas.create_window((0, 0), window=frame, anchor="nw")
            self.canvas.yview_moveto('0')
            return frame

        def load_parameters():
            try:
                self.parameters = pickle.load(open("parameters.pickle", "rb"))
                self.pwdir = self.parameters['pwdir']
            except:
                self.pwdir = ""

        def title():
            # title
            tk.Label(self.frame, text='LaharZ', font=('Helvetica', 14, 'bold')).grid(row=0, column = 0, padx = 10, columnspan=1, sticky='NW')
            
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=1, column = 0, padx = 10, columnspan=1, sticky='NW')

        def working_sub_directory():

            tk.Label(self.frame, text='Sub Directory', font=('Helvetica', 12)).grid(row=2, column = 0, padx = 10, columnspan=1, sticky='NW')
            
            self.tk_pwdir = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pwdir.grid(row=2, column = 1, padx = 10, columnspan=1, sticky='NW')
            self.tk_pwdir.focus_set()
        
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=1, column = 0, padx = 10, columnspan=1, sticky='NW')

            self.tk_pwdir.insert(0, self.pwdir)
            self.tk_pwdir_msg = tk.Label(self.frame, text = '', font=('Helvetica', 12))
            self.tk_pwdir_msg.grid(row=2, column=2, padx = 10, columnspan=1, sticky='W')

            tk.Label(self.frame, text='Your current directory is:' , font=('Helvetica', 10, 'italic')).grid(row=3, column = 0, padx = 10, columnspan=2, sticky='NW')
            tk.Label(self.frame, text=os.getcwd(), font=('Helvetica', 10, 'italic')).grid(row=4, column = 0, padx = 10, columnspan=2, sticky='NW')
            
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=5, column = 0, padx = 10, columnspan=1, sticky='NW')
       
        def create_initiation_points_button():
            self.tk_cip_button = tk.Button(self.frame, text='Create Initiation Points', font=('Helvetica', 12,), height = 5, width = 40, bg = '#0056B9', borderwidth = 0)
            self.tk_cip_button.grid(row=10, column = 0, padx = 40, pady = 0, columnspan=2, sticky='W')
            self.tk_cip_button['command'] = press_cip_button


        def create_lahars_button():
            # blank line            
            self.tk_cl_button = tk.Button(self.frame, text='Create Flow Outputs', font=('Helvetica', 12), height = 5, width = 40, bg = '#FFD800', borderwidth = 0)
            self.tk_cl_button.grid(row=11, column = 0, padx = 40, pady = 0, columnspan=2, sticky='W')
            self.tk_cl_button['command'] = press_cl_button
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=15, column = 0, padx = 10, pady = 0, columnspan=1, sticky='NW')

        def exit_button():
            self.tk_exit_button = tk.Button(self.frame, text='Exit', font=('Helvetica', 12))
            self.tk_exit_button.grid(row=20, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_exit_button['command'] = press_exit_button

        def status_msg():
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=50, column = 0, padx = 10, columnspan=1, sticky='NW')

            self.tk_statusmsg = tk.Label(self.frame, text = self.sts_msg, font=('Helvetica', 12), justify = 'left')
            self.tk_statusmsg.grid(row=51, column = 0, padx = 10, columnspan=4, sticky='W')
            self.tk_statusmsg2 = tk.Label(self.frame, text = self.sts_msg2, font=('Helvetica', 10, "italic"), justify = 'left')
            self.tk_statusmsg2.grid(row=52, column = 0, padx = 10, columnspan=4, sticky='W')

        def validate_pwdir():
            self.pwdir = self.tk_pwdir.get()
            self.sts_msg = ""
            self.sts_msg2 = ""
            self.pwdir, error, self.tk_pwdir_msg['text'] = validate_dir_to_read(self.pwdir)
            self.tk_pwdir.delete(0, "end") #update file name on screen post validation
            self.tk_pwdir.insert(0, self.pwdir)

            if error:
                self.tk_pwdir_msg['fg'] = "red"
            return error
            
        def press_cip_button():
            error = validate_pwdir()
            if not error:
                # Save parameters
                self.parameters = {}
                self.parameters["pwdir"]  = self.pwdir
                pickle.dump(self.parameters, open("parameters.pickle", "wb"))
                self.frame.destroy()
                self.exec_frame2()

        def press_cl_button():
            error = validate_pwdir()
            if not error:
                # Save parameters
                self.parameters = {}
                self.parameters["pwdir"]  = self.pwdir
                pickle.dump(self.parameters, open("parameters.pickle", "wb"))
                self.frame.destroy()
                self.exec_frame3()

        def press_exit_button():
            self.destroy()

        load_parameters()
        self.frame = create_frame()
        title()
        working_sub_directory()
        create_initiation_points_button()
        create_lahars_button()
        exit_button()
        status_msg()

    def exec_frame2(self):
        def create_frame():
            # Create a frame on the canvas to contain the widgets
            frame = tk.Frame(self.canvas)
            frame.columnconfigure((0,1,2,3), weight = 1)
            frame.rowconfigure(0, weight = 1)
            frame.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = tk.NW)
            frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            self.canvas.create_window((0, 0), window=frame, anchor="nw")
            self.canvas.yview_moveto('0')

            return frame

        def title(r):
            # title
            tk.Label(self.frame, text='Generate Initiation Points', font=('Helvetica', 14, 'bold')).grid(row=r, column = 0, padx = 10, columnspan=1, sticky='NW')
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r+1, column = 0, padx = 10, columnspan=1, sticky='NW')

        def DEM_file(r):
            tk.Label(self.frame, text='DEM File', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pdem_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pdem_fn.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pdem_fn.insert(0, self.pdem_fn)
            self.tk_pdem_fn_msg = tk.Label(self.frame, text='Name of your DEM file in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pdem_fn_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def thal_file(r):
            tk.Label(self.frame, text='Streams File', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pthal_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pthal_fn.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pthal_fn.insert(0, self.pthal_fn)
            self.tk_pthal_fn_msg = tk.Label(self.frame, text='Name of your streams file in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pthal_fn_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r+1, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')

        def apex_choice(r):
            tk.Label(self.frame, text='Determine Energy Cone Apex', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_papex_choice = tk.StringVar()
            self.tk_papex_choice.set(self.papex_choice)
            tk.Radiobutton(self.frame, text='Use Search File', font=('Helvetica', 12), variable=self.tk_papex_choice, value='Search', command = choose_search) \
                .grid(row=r+1, column = 0, padx = 10, columnspan=1, sticky='W')
            tk.Radiobutton(self.frame, text='Use Longitude/Latitude', font=('Helvetica', 12), variable=self.tk_papex_choice, value='LatLon', command = choose_latlon) \
                .grid(row=r+2, column = 0, padx = 10, columnspan=1, sticky='W')
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r+3, column = 0, padx = 10, columnspan=1, sticky='W')

        def overwrite_message1(r):
            self.tk_overwrite_message1 = tk.Label(self.frame, text = 'Uncheck box to disable overwrite check', font=('Helvetica', 10, 'italic'))
            self.tk_overwrite_message1.grid(row=r, column = 1, padx = 10, columnspan=2, sticky='W')

        def overwrite_message2(r):
            self.tk_overwrite_message2 = tk.Label(self.frame, text = 'Uncheck box to disable overwrite check', font=('Helvetica', 10, 'italic'))
            self.tk_overwrite_message2.grid(row=r, column = 1, padx = 10, columnspan=2, sticky='W')

        def choose_latlon():
            self.tk_overwrite_message1.grid_forget()
            self.tk_psearch_fn_lbl.grid_forget()
            self.tk_sf_ow_chk.grid_forget()
            self.tk_psearch_fn.grid_forget()
            self.tk_psearch_fn_msg.grid_forget()
            self.tk_new_sf_button.grid_forget()
            self.tk_pnew_sf_msg.grid_forget()

            self.tk_psearch_option_lbl.grid_forget()
            self.tk_psearch_option1.grid_forget()
            self.tk_psearch_option2.grid_forget()
            self.tk_psearch_option3.grid_forget()
            self.tk_psearch_option_msg.grid_forget()

            try:
                self.tk_psearch_box_size_lbl.grid_forget()
                self.tk_psearch_box_size.grid_forget()
                self.tk_psearch_box_size_msg.grid_forget()
                self.tk_pentry_point_lbl.grid_forget()
                self.tk_pentry_point.grid_forget()
                self.tk_pentry_point_msg.grid_forget()
                self.tk_sf_button.grid_forget()
            except:
                pass

            self.papex_choice = self.tk_papex_choice.get()

            get_apex(40)

        def get_apex(r):
            self.tk_papex_lbl = tk.Label(self.frame, text='Apex', font=('Helvetica', 12))
            self.tk_papex_lbl.grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_papex = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_papex.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_papex.insert(0, ', '.join(str(x) for x in self.papex)) #converts list to csv string
            self.tk_papex_msg = tk.Label(self.frame, text='Longitude, Latitude', font=('Helvetica', 12))
            self.tk_papex_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def get_entry_point(r):
            self.tk_pentry_point_lbl = tk.Label(self.frame, text='Centre Point', font=('Helvetica', 12))
            self.tk_pentry_point_lbl.grid(row=r, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_pentry_point = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pentry_point.grid(row=r, column = 2, padx = 10, columnspan=1, sticky='W')
            self.tk_pentry_point.insert(0, ', '.join(str(x) for x in self.pentry_point)) #converts list to csv string
            self.tk_pentry_point_msg = tk.Label(self.frame, text='Longitude, Lattitude', font=('Helvetica', 12))
            self.tk_pentry_point_msg.grid(row=r, column = 3, padx = 10, columnspan=1, sticky='W')

        def choose_search():
            try:
                self.tk_papex_lbl.grid_forget()
                self.tk_papex.grid_forget()
                self.tk_papex_msg.grid_forget()
            except:
                pass
            self.papex_choice = self.tk_papex_choice.get()
            overwrite_message1(45)
            search_file(50)
            new_sf_button(55)
            search_option(70)

        def search_file(r):
            self.tk_psearch_fn_lbl =  tk.Label(self.frame, text='Search File', font=('Helvetica', 12))
            self.tk_psearch_fn_lbl.grid(row=r, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_sf_ow = tk.BooleanVar(value = self.psf_ow)
            self.tk_sf_ow_chk = tk.Checkbutton(self.frame, text='', font=('Helvetica', 12), variable=self.tk_sf_ow)
            self.tk_sf_ow_chk.grid(row=r, column = 1, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_psearch_fn.grid(row=r, column = 2, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_fn.insert(0, self.psearch_fn)
            self.tk_psearch_fn_msg = tk.Label(self.frame, text='Name of your Search file in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_psearch_fn_msg.grid(row=r, column = 3, padx = 10, columnspan=1, sticky='W')
       
        def search_box_size(r):
            self.tk_psearch_box_size_lbl = tk.Label(self.frame, text='Search Area Size', font=('Helvetica', 12))
            self.tk_psearch_box_size_lbl.grid(row=r, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_box_size = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_psearch_box_size.grid(row=r, column = 2, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_box_size.insert(0, self.psearch_box_size)
            self.tk_psearch_box_size_msg = tk.Label(self.frame, text='Search area size (m)', font=('Helvetica', 12))
            self.tk_psearch_box_size_msg.grid(row=r, column = 3, padx = 10, columnspan=1, sticky='W')

        def new_sf_button(r):
            self.tk_psearch_fn['state']= 'normal'
            self.tk_new_sf_button = tk.Button(self.frame, text='New Search File', font=('Helvetica', 12))
            self.tk_new_sf_button.grid(row=r+1, column = 2, padx = 10, columnspan=1, sticky='W')
            self.tk_new_sf_button['command'] = press_new_sf_button
            self.tk_pnew_sf_msg = tk.Label(self.frame, text='Press to create new Search file in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pnew_sf_msg.grid(row=r+1, column = 3, padx = 10, columnspan=1, sticky='W')

        def press_new_sf_button():

            self.tk_pnew_sf_msg['text'] = ""
            self.tk_statusmsg['text'] = ""
            error = True in {validate_DEM(), validate_thal()}
            if error:
                self.tk_statusmsg["text"] = "Please correct errors before continuing"
                self.tk_statusmsg['fg'] = "red"
                return

            error, cancel_flag = validate_new_search_file()
            if error:
                self.tk_statusmsg["text"] = "Please correct errors before continuing"
                self.tk_statusmsg['fg'] = "red"
                return

            if not cancel_flag:
                self.tk_new_sf_button.grid_forget()
                self.tk_pnew_sf_msg.grid_forget()
                self.tk_psearch_fn_msg['text'] = ""
                self.tk_psearch_fn['state']= 'disabled'
                save_parameters()
                get_entry_point(55)
                search_box_size(60)
                create_sf_button(65)
                cancel_sf_button(65)
            return

        def create_sf_button(r):
            self.tk_sf_button = tk.Button(self.frame, text='Create Search File', font=('Helvetica', 12))
            self.tk_sf_button.grid(row=r, column = 2, padx = 10, columnspan=1, sticky='W')
            self.tk_sf_button['command'] = press_create_sf_button

        def cancel_sf_button(r):
            self.tk_sfc_button = tk.Button(self.frame, text='Cancel', font=('Helvetica', 12))
            self.tk_sfc_button.grid(row=r, column = 3, padx = 10, columnspan=1, sticky='W')
            self.tk_sfc_button['command'] = press_cancel_sf_button

        def press_create_sf_button():
            error = True in {validate_DEM(),validate_thal(), validate_entry_point(), validate_search_box_size()}
            if error:
                self.tk_statusmsg["text"] = "Please correct errors before continuing"
                self.tk_statusmsg['fg'] = "red"
            else:
                self.tk_statusmsg["text"] = ""
                self.tk_pentry_point.grid_forget()
                self.tk_pentry_point_lbl.grid_forget()
                self.tk_pentry_point_msg.grid_forget()
                self.tk_psearch_box_size.grid_forget()
                self.tk_psearch_box_size_msg.grid_forget()
                self.tk_psearch_box_size_lbl.grid_forget()
                self.tk_sf_button.grid_forget()
                self.tk_sfc_button.grid_forget()
                new_sf_button(55)
                create_new_sf()
                save_parameters()

        def press_cancel_sf_button():
            self.tk_statusmsg["text"] = ""
            self.tk_pentry_point.grid_forget()
            self.tk_pentry_point_lbl.grid_forget()
            self.tk_pentry_point_msg.grid_forget()
            self.tk_psearch_box_size.grid_forget()
            self.tk_psearch_box_size_lbl.grid_forget()
            self.tk_psearch_box_size_msg.grid_forget()
            self.tk_sf_button.grid_forget()
            self.tk_sfc_button.grid_forget()

            self.tk_psearch_fn['state']= 'normal'
            self.tk_psearch_fn_msg['text']= ''
            new_sf_button(55)
            
        def create_new_sf():
            ep = shPoint(self.pentry_point_x, self.pentry_point_y)
            d = self.psearch_box_size/2 *2**.5
            x1, y1 = lltransform([self.pentry_point_x, self.pentry_point_y], d, -135)
            x2, y2 = lltransform([self.pentry_point_x, self.pentry_point_y], d, 45)

            geoms = [ep, Polygon(((x1, y1), (x1, y2), (x2, y2), (x2, y1)))]
            index = ["Centre", "Search Area"]
            psearch_fn = os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), self.psearch_fn])

            gds = gpd.GeoSeries(geoms, index, crs="EPSG:4326")
            gds.to_file(psearch_fn, driver="GPKG") #ffff
            log_msg("Created new search file: " + psearch_fn, screen_op = False)

            # Also tried with Fiona but it can't manage points and ploygons together but can name the layer
            # schema = {
            #     'geometry': 'Point',
            #     'properties': {'label': 'str'}
            #         }

            # with fiona.open('Coto22/fionatest2.gpkg', 'w', driver='GPKG', crs=from_epsg(4326), schema=schema, layer='Search') as dst:
            #     dst.write({'geometry': {'type': 'Point', 'coordinates': (-78.44, -0.68)}, 'properties': {'label': "Entry Point"}})

            self.tk_pnew_sf_msg["text"] = "Search file " + self.psearch_fn + " created in " + self.pwdir

        def search_option(r):
            # self.tk_psearch_option_blk = tk.Label(self.frame, text = '', font=('Helvetica', 12))
            # self.tk_psearch_option_blk.grid(row=r-1, column = 3, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_option_lbl = tk.Label(self.frame, text='Search Option', font=('Helvetica', 12))
            self.tk_psearch_option_lbl.grid(row=r, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_option = tk.StringVar()
            self.tk_psearch_option.set(self.psearch_option)
            self.tk_psearch_option1 = tk.Radiobutton(self.frame, text='Use Highest Point in Search Area', font=('Helvetica', 12), variable=self.tk_psearch_option, value='Highest Point')
            self.tk_psearch_option1.grid(row=r+1, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_option2 = tk.Radiobutton(self.frame, text='Use Centre of Search Area', font=('Helvetica', 12), variable=self.tk_psearch_option, value='Centre')
            self.tk_psearch_option2.grid(row=r+2, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_option3 = tk.Radiobutton(self.frame, text='Use Point \'Centre\'', font=('Helvetica', 12), variable=self.tk_psearch_option, value='Centre Point')
            self.tk_psearch_option3.grid(row=r+3, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_psearch_option_msg = tk.Label(self.frame, text = '', font=('Helvetica', 12))
            self.tk_psearch_option_msg.grid(row=r+1, column = 3, padx = 10, columnspan=1, sticky='W')
            
        def incremental_height(r):
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r-1, column=0, padx = 10, columnspan=1, sticky='W')
            tk.Label(self.frame, text='Incremental Height', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pincremental_height = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pincremental_height.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pincremental_height.insert(0, self.pincremental_height)
            self.tk_pincremental_height_msg = tk.Label(self.frame, text='Incremental height in metres',font=('Helvetica', 12))
            self.tk_pincremental_height_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def hlratio(r):
            tk.Label(self.frame, text='H/L Ratio', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_phlratio = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_phlratio.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_phlratio.insert(0, self.phlratio)
            self.tk_phlratio_msg = tk.Label(self.frame, text='H/L Ratio',font=('Helvetica', 12))
            self.tk_phlratio_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r+1, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')

        def plot_mesh(r):
            self.tk_pplot_mesh = tk.BooleanVar(value = self.pplot_mesh)
            tk.Checkbutton(self.frame, text='Plot Energy Cone Graphics', font=('Helvetica', 12), variable=self.tk_pplot_mesh, command = choose_plot_mesh).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pplot_mesh_msg = tk.Label(self.frame, text = '', font=('Helvetica', 12))
            self.tk_pplot_mesh_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def choose_plot_mesh():
            self.pplot_mesh = self.tk_pplot_mesh.get()
            if self.pplot_mesh:
                self.tk_overwrite_message2.grid_forget()
                overwrite_message2(100)
                ec_graphics_fn(105)
                mesh_extent(115)

            else:
                self.tk_pec_graphics_fn_lbl.grid_forget()
                self.tk_pec_graphics_fn.grid_forget()
                self.tk_pec_graphics_fn_msg.grid_forget()
                self.tk_pmesh_extent_lbl.grid_forget()
                self.tk_pmesh_extent.grid_forget()
                self.tk_pmesh_extent_msg.grid_forget()
                self.tk_pmesh_extent_blk.grid_forget()
                self.tk_ecgf_ow_chk.grid_forget()
                self.tk_overwrite_message2.grid_forget()
                overwrite_message2(103)

        def ec_graphics_fn(r):
            self.tk_pec_graphics_fn_lbl = tk.Label(self.frame, text='Energy Cone Graphics File', font=('Helvetica', 12))
            self.tk_pec_graphics_fn_lbl.grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_ecgf_ow = tk.BooleanVar(value = self.pecgf_ow)
            self.tk_ecgf_ow_chk = tk.Checkbutton(self.frame, text='', font=('Helvetica', 12), variable=self.tk_ecgf_ow)
            self.tk_ecgf_ow_chk.grid(row=r, column = 1, padx = 10, columnspan=1, sticky='W')

            self.tk_pec_graphics_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pec_graphics_fn.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pec_graphics_fn.insert(0, self.pec_graphics_fn)
            self.tk_pec_graphics_fn_msg = tk.Label(self.frame, text='Name of the file for the energy cone graphics in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pec_graphics_fn_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def mesh_extent(r):
            self.tk_pmesh_extent_lbl = tk.Label(self.frame, text='Extent', font=('Helvetica', 12))
            self.tk_pmesh_extent_lbl.grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pmesh_extent = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pmesh_extent.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pmesh_extent.insert(0, self.pmesh_extent)
            self.tk_pmesh_extent_msg = tk.Label(self.frame, text='Extent to plot the energy cone/surface (1.3 = 130% of L)',font=('Helvetica', 12))
            self.tk_pmesh_extent_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pmesh_extent_blk = tk.Label(self.frame, text = '' , font=('Helvetica', 12))
            self.tk_pmesh_extent_blk.grid(row=r+1, column=0, padx = 10, pady = 3, columnspan=1, sticky='W')

        def ecline_file(r):
            # tk.Label(self.frame, text = '' , font=('Helvetica', 12)).grid(row=r, column=0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pecline_fn_lbl =  tk.Label(self.frame, text='Energy Cone Line File', font=('Helvetica', 12))
            self.tk_pecline_fn_lbl.grid(row=r+1, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_ec_ow = tk.BooleanVar(value = self.pec_ow)
            tk.Checkbutton(self.frame, text='', font=('Helvetica', 12), variable=self.tk_ec_ow).grid(row=r+1, column = 1, padx = 10, columnspan=1, sticky='W')

            self.tk_pecline_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pecline_fn.grid(row=r+1, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pecline_fn.insert(0, self.pecline_fn)
            self.tk_pecline_fn_msg = tk.Label(self.frame, text='Name of the file for the energy cone line in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pecline_fn_msg.grid(row=r+1, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def initpoints_file(r):
            self.tk_pinitpoints_fn_lbl =  tk.Label(self.frame, text='Initiation Points File', font=('Helvetica', 12))
            self.tk_pinitpoints_fn_lbl.grid(row=r+1, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_ip_ow = tk.BooleanVar(value = self.pip_ow)
            tk.Checkbutton(self.frame, text='', font=('Helvetica', 12), variable=self.tk_ip_ow).grid(row=r+1, column = 1, padx = 10, columnspan=1, sticky='W')
            self.tk_pinitpoints_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pinitpoints_fn.grid(row=r+1, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pinitpoints_fn.insert(0, self.pinitpoints_fn)
            self.tk_pinitpoints_fn_msg = tk.Label(self.frame, text='Name of the file for the initiations points in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pinitpoints_fn_msg.grid(row=r+1, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text = '' , font=('Helvetica', 12)).grid(row=r+2, column=0, padx = 10, pady = 3, columnspan=1, sticky='W')

        def back_button(r):
            self.tk_back_button = tk.Button(self.frame, text='Back', font=('Helvetica', 12))
            self.tk_back_button.grid(row=r, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_back_button['command'] = press_back_button

        def press_back_button():
            self.frame.destroy()
            self.exec_frame1()

        def ip_button(r):
            self.tk_ip_button = tk.Button(self.frame, text='Initiation points', font=('Helvetica', 12))
            self.tk_ip_button.grid(row=r, column = 2, padx = 10, columnspan=1, sticky='W')
            self.tk_ip_button['command'] = press_ip_button

        def press_ip_button():
            self.tk_statusmsg["text"] = ""
            error = True in {validate_DEM(), validate_thal(), validate_incremental_height(), validate_hlratio()}
            if self.papex_choice == 'LatLon':
                error = True in {validate_apex(), error}
            elif self.papex_choice == 'Search':
                error = True in {validate_search_file(), validate_search_options(), error}
            if self.pplot_mesh:
                error = True in {validate_mesh_extent(), error}
            error2 = []
            cancel_flag = []
            i = 0
            while i <3 and not any(cancel_flag):
                if i == 0:
                    if self.pplot_mesh:
                        e, cf = validate_ec_graphics_fn()
                    else:
                        e, cf = False, False
                if i == 1:
                    e, cf = validate_ecline_file()
                if i == 2:
                    e, cf = validate_initpoints_file()
                error2.append(e)
                cancel_flag.append(cf)
                i += 1

            if error or any(error2):
                self.tk_statusmsg["text"] = "Please correct errors before continuing"
                self.tk_statusmsg['fg'] = "red"
                return
            if not any(cancel_flag):
                save_parameters()
                self.tk_statusmsg["text"] = "Creating initiation points..."
                self.tk_statusmsg['fg'] = "black"
                self.update()
                error = create_initiation_points()
                if not error: 
                    ip_conf_window()
                    self.frame.destroy()
                    self.exec_frame1() #start

        def ip_conf_window():
                # freeze frame
                for child in self.frame.winfo_children():
                        child.configure(state='disabled')

                # create pop out from frame
                po_toplvl = tk.Toplevel()
                po_toplvl.columnconfigure(0, weight = 1)
                po_toplvl.rowconfigure(0, weight = 1)
                po_toplvl['borderwidth'] = 50

                frame1 = tk.Frame(po_toplvl)
                frame1.columnconfigure(0, weight = 1)
                frame1.rowconfigure(0, weight = 1)
                frame1.grid(row = 0, column = 0, padx = 10, sticky=tk.NSEW)

                tk.Label(frame1, text="Initiation points created", font=('Helvetica', 12, 'bold')).grid(row=10, column = 0, padx = 10, columnspan=2, sticky='W')
                tk.Label(frame1, text='You can edit the initiation points file, ' + self.pinitpoints_fn + ', in QGIS before continuing, if you wish', font=('Helvetica', 12)).grid(row=20, column = 0, padx = 10, pady = 10, columnspan=2, sticky='W')

                tk_proceed_button = tk.Button(frame1, text="Continue", font=('Helvetica', 12), command = lambda : proceed.set(True))
                tk_proceed_button.grid(row=30, column = 0, padx = 10, pady = 20, columnspan=1)

                #pause execution until button is pressed
                proceed = tk.BooleanVar()
                proceed.set(False)
                tk_proceed_button.wait_variable(proceed)

                #unfreeze frame
                for child in self.frame.winfo_children():
                        child.configure(state='normal')
                #remove pop up
                po_toplvl.destroy()

        def status_msg(r):
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, columnspan=1, sticky='NW')

            self.tk_statusmsg = tk.Label(self.frame, text = "", fg = "green", font=('Helvetica', 12))
            self.tk_statusmsg.grid(row=r+1, column = 0, columnspan=6, sticky='W')

        def validate_DEM():
            self.pdem_fn = self.tk_pdem_fn.get()
            self.pdem_fn, error, self.tk_pdem_fn_msg['text'] = validate_file_to_read(self.pdem_fn, self.pwdir, type = 'tif')
            self.tk_pdem_fn.delete(0, "end") #update file name on screen post validation
            self.tk_pdem_fn.insert(0, self.pdem_fn)

            if error:
                self.tk_pdem_fn_msg['fg'] = 'red'
            return error

        def validate_thal():
            self.pthal_fn = self.tk_pthal_fn.get()
            self.pthal_fn, error, self.tk_pthal_fn_msg['text'] = validate_file_to_read(self.pthal_fn, self.pwdir, type = 'tif')
            self.tk_pthal_fn.delete(0, "end") #update file name on screen post validation
            self.tk_pthal_fn.insert(0, self.pthal_fn)

            if error:
                self.tk_pthal_fn_msg['fg'] = 'red'
            return error

        def validate_search_file():
            # Search file
            self.psearch_fn = self.tk_psearch_fn.get()
            self.tk_pnew_sf_msg['text'] = ""
            self.psearch_fn, error, self.tk_psearch_fn_msg['text'] = validate_file_to_read(self.psearch_fn, self.pwdir, type = "gpkg")
            self.tk_psearch_fn.delete(0, "end") #update file name on screen post validation
            self.tk_psearch_fn.insert(0, self.psearch_fn)

            if error:
                self.tk_psearch_fn_msg['fg'] = "red"
            return error

        def validate_new_search_file():
            # Search file
            self.tk_psearch_fn_msg['text'] = ""
            self.psearch_fn = self.tk_psearch_fn.get()
            self.psf_ow = self.tk_sf_ow.get()
            self.psearch_fn, error, cancel_flag, self.tk_psearch_fn_msg['text'] = validate_file_to_write(self.psearch_fn, self.pwdir, self.frame, "Search File", extend = 'gpkg', type = "gpkg", exists = self.psf_ow)
            self.tk_psearch_fn.delete(0, "end") #update file name on screen post validation
            self.tk_psearch_fn.insert(0, self.psearch_fn)
            if error:
                self.tk_psearch_fn_msg['fg'] = "red"
                return error, cancel_flag
    
            if cancel_flag:
                return False, True
            
            self.pow_search_fn = self.psearch_fn
            return False, False

        def validate_apex():
            error = False
            self.tk_papex_msg['text'] = ""

            self.papex = self.tk_papex.get()
            papex = self.tk_papex.get().split(",") #working variable

            #convert to numeric
            papex2 = []
            for i in papex:
                try:
                    papex2 += [float(i),]
                except:
                    self.tk_papex_msg['text'] = "Error: Values must be numeric"
                    self.tk_papex_msg['fg'] = "red"
                    return True

            papex = papex2
            if len(papex) != 2:
                self.tk_papex_msg['text'] = "Error: Only 2 values (Longitude, Lattitude) accepted"
                self.tk_papex_msg['fg'] = "red"
                return True
            if papex[0] <-180 or papex[0]>180:
                self.tk_papex_msg['text'] = "Error: Longitude outside of normal range of -180 to 180 degrees"
                self.tk_papex_msg['fg'] = "red"
                return True
            if papex[1] <-90 or papex[1]>90:
                self.tk_papex_msg['text'] = "Error: Latitude outside of normal range of -90 to 90 degrees"
                self.tk_papex_msg['fg'] = "red"
                return True
            self.papex = papex
            return False

        def validate_entry_point():
            # can't validate if entry point is in DEM as DEM file has not been opened yet.
            error = False
            self.tk_pentry_point_msg['text'] = ""
            self.pentry_point = self.tk_pentry_point.get()
            pentry_point = self.tk_pentry_point.get().split(",") #working variable

            #convert to numeric
            pentry_point2 = []
            for i in pentry_point:
                try:
                    pentry_point2 += [float(i),]
                except:
                    self.tk_pentry_point_msg['text'] = "Error: Values must be numeric"
                    self.tk_pentry_point_msg['fg'] = "red"
                    error = True

            if not error:
                pentry_point = pentry_point2
                if len(pentry_point) != 2:
                    self.tk_pentry_point_msg['text'] = "Error: Only 2 values (Longitude, Latitude) accepted"
                    self.tk_pentry_point_msg['fg'] = "red"
                    error = True
                else:
                    if pentry_point[0] <-180 or pentry_point[0]>180:
                        self.tk_pentry_point_msg['text'] = "Error: Longitude outside of normal range of -180 to 180 degrees"
                        self.tk_pentry_point_msg['fg'] = "red"
                        error = True
                    if pentry_point[1] <-90 or pentry_point[1]>90:
                        self.tk_pentry_point_msg['text'] = "Error: Latitude outside of normal range of -90 to 90 degrees"
                        self.tk_pentry_point_msg['fg'] = "red"
                        error = True
            if not error:
                self.pentry_point_x = pentry_point[0]
                self.pentry_point_y = pentry_point[1]

            self.pentry_point = pentry_point
            return error
        
        def validate_search_box_size():
            self.tk_psearch_box_size_msg['text'] = ""
            error = False

            self.psearch_box_size = self.tk_psearch_box_size.get()
            if self.psearch_box_size == '':
                self.psearch_box_size = 0

            self.psearch_box_size, error, self.tk_psearch_box_size_msg['text']  = validate_numeric(self.psearch_box_size, zero = True, gt = 0)
            if error:
                self.tk_psearch_box_size_msg['fg'] = "red"

            return error

        def validate_search_options():
            self.psearch_option = self.tk_psearch_option.get()
            if self.psearch_option == "":
                self.tk_psearch_option_msg['text'] = "Please choose at least one option"
                self.tk_psearch_option_msg['fg'] = "red"
                error = True
            else:
                self.tk_psearch_option_msg['text'] = ""
    
        def validate_incremental_height():
            self.tk_pincremental_height_msg['text'] = ""

            self.pincremental_height = self.tk_pincremental_height.get()
            self.pincremental_height, error, self.tk_pincremental_height_msg['text'] = validate_numeric(self.pincremental_height, zero = True)
            self.tk_pincremental_height.delete(0, "end") #update file name on screen post validation
            self.tk_pincremental_height.insert(0, self.pincremental_height)

            if error:
                self.tk_pincremental_height_msg['fg'] = "red"
            return error

        def validate_hlratio():
            self.tk_phlratio_msg['text'] = ""

            self.phlratio = self.tk_phlratio.get()
            if not sys_parms['povr_hl_ratio'][0]:
                self.phlratio, error, self.tk_phlratio_msg['text'] = validate_numeric(self.phlratio, range = (0.1, 0.3))
            else:
                self.phlratio, error, self.tk_phlratio_msg['text'] = validate_numeric(self.phlratio, gt = 0)

            if error:
                self.tk_phlratio_msg['fg'] = "red"

            return error
        
        def validate_ec_graphics_fn():
            self.tk_pec_graphics_fn_msg['text'] = ""
            self.pec_graphics_fn = self.tk_pec_graphics_fn.get()
            self.pecgf_ow = self.tk_ecgf_ow.get()
            self.pec_graphics_fn, error, cancel_flag, self.tk_pec_graphics_fn_msg['text'] = \
                validate_file_to_write(self.pec_graphics_fn, self.pwdir, self.frame, 
                                       "Energy Cone Graphics File", exists = self.pecgf_ow, extend = 'tif', type = 'tif')
            if error:
                self.tk_pec_graphics_fn_msg['fg'] = "red"
            return error, cancel_flag

        def validate_mesh_extent():
            self.tk_pmesh_extent_msg['text'] = ""

            self.pmesh_extent = self.tk_pmesh_extent.get()
            self.pmesh_extent, error, self.tk_pmesh_extent_msg['text'] = validate_numeric(self.pmesh_extent, gt = 0, zero = True)

            if error:
                self.tk_pmesh_extent_msg['fg'] = "red"

            return error

        def validate_ecline_file():
            self.tk_pecline_fn_msg['text'] = ""
            self.pecline_fn = self.tk_pecline_fn.get()
            self.pec_ow = self.tk_ec_ow.get()
            self.pecline_fn, error, cancel_flag, self.tk_pecline_fn_msg['text'] = \
                validate_file_to_write(self.pecline_fn, self.pwdir, self.frame, "Enery Cone Line file", extend = 'tif', type = 'tif', exists = self.pec_ow)
            self.tk_pecline_fn.delete(0, "end") #update file name on screen post validation
            self.tk_pecline_fn.insert(0, self.pecline_fn)
            if not error and not cancel_flag:
                self.pow_ecline_fn = self.pecline_fn
            if error:
                self.tk_pecline_fn_msg['fg'] = "red"
            return error, cancel_flag

        def validate_initpoints_file():
            self.tk_pinitpoints_fn_msg['text'] = ""
            self.pinitpoints_fn = self.tk_pinitpoints_fn.get()
            self.pip_ow = self.tk_ip_ow.get()
            self.pinitpoints_fn, error, cancel_flag, self.tk_pinitpoints_fn_msg['text'] = \
                validate_file_to_write(self.pinitpoints_fn, self.pwdir, self.frame, "Initiation Points file", extend = 'gpkg', type = 'gpkg', exists = self.pip_ow)
            self.tk_pinitpoints_fn.delete(0, "end") #update file name on screen post validation
            self.tk_pinitpoints_fn.insert(0, self.pinitpoints_fn)
            if not error and not cancel_flag:
                self.pow_initpoints_fn = self.pinitpoints_fn
            if error:
                self.tk_pinitpoints_fn_msg['fg'] = "red"
            return error, cancel_flag
       
        def save_parameters():
            self.parameters['pdem_fn'] = self.pdem_fn
            self.parameters['pthal_fn'] = self.pthal_fn
            self.parameters['papex_choice'] = self.papex_choice
            self.parameters['papex'] = self.papex
            self.parameters['pentry_point'] = self.pentry_point
            self.parameters['pincremental_height'] = self.pincremental_height
            self.parameters['phlratio'] = self.phlratio
            self.parameters['pecline_fn'] = self.pecline_fn
            self.parameters['pinitpoints_fn'] = self.pinitpoints_fn
            self.parameters['pplot_mesh'] = self.pplot_mesh
            self.parameters['pec_graphics_fn'] = self.pec_graphics_fn
            self.parameters['pmesh_extent'] = self.pmesh_extent
            self.parameters['psearch_fn'] = self.psearch_fn
            self.parameters['psearch_box_size'] = self.psearch_box_size
            self.parameters['psearch_option'] = self.psearch_option
            self.parameters['psf_ow'] = self.psf_ow
            self.parameters['pecgf_ow'] = self.pecgf_ow
            self.parameters['pec_ow'] = self.pec_ow
            self.parameters['pip_ow'] = self.pip_ow

            pickle.dump(self.parameters, open(os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), "parameters.pickle"]), "wb"))

        def load_parameters():
            # Load Parameters
            try:
                self.parameters = pickle.load(open(os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), "parameters.pickle"]), "rb"))
            except:
                self.parameters = {}
            
            try:
                self.pdem_fn = self.parameters['pdem_fn']
                self.pthal_fn = self.parameters['pthal_fn']
                self.papex_choice = self.parameters['papex_choice']
                self.papex = self.parameters['papex']
                self.pentry_point = self.parameters['pentry_point']
                self.pincremental_height = self.parameters['pincremental_height']
                self.phlratio = self.parameters['phlratio']
                self.pinitpoints_fn = self.parameters['pinitpoints_fn']
                self.pecline_fn = self.parameters['pecline_fn']
                self.pplot_mesh = self.parameters['pplot_mesh']
                self.pec_graphics_fn = self.parameters['pec_graphics_fn']
                self.pmesh_extent = self.parameters['pmesh_extent']
                self.psearch_fn = self.parameters['psearch_fn']
                self.psearch_box_size = self.parameters['psearch_box_size']
                self.psearch_option = self.parameters['psearch_option']
                self.psf_ow = self.parameters['psf_ow']
                self.pecgf_ow = self.parameters['pecgf_ow']
                self.pec_ow = self.parameters['pec_ow']
                self.pip_ow = self.parameters['pip_ow']
            except:
                self.pdem_fn = ""
                self.pthal_fn = ""
                self.papex_choice = "Search"
                self.psearch_fn = ""
                self.papex = ""
                self.pentry_point = ""
                self.pincremental_height = ""
                self.phlratio = .2
                self.pecline_fn = "ec_line.tif"
                self.pinitpoints_fn = ""
                self.pplot_mesh = True
                self.pec_graphics_fn = "ec_cone.tif"
                self.pmesh_extent = "1.3"
                self.psearch_box_size = ""
                self.psearch_fn = ""
                self.psearch_option = "Highest Point"
                self.psf_ow = True
                self.pecgf_ow = True
                self.pec_ow = True
                self.pip_ow = True

            
            self.pow_search_fn = ""
            self.pow_ecline_fn = ""
            self.pow_ec_graphics_fn = ""
            self.pow_initpoints_fn = ""

        def create_initiation_points():

            def create_ips(apex, *args):

                def op_ec_points(ec_points, ec_fn):
                    """Dumps out all points on the energy cone line for debugging"""
                    ec_fn = os.sep.join([os.getcwd(), self.pwdir, ec_fn])
                    try:
                        epcsv = csv.writer(open(ec_fn, "w", newline = ""), delimiter=',', dialect="excel", quoting=csv.QUOTE_MINIMAL)
                        epcsv.writerow(["Label", "Longitude", "Latitude", "Row", "Column"])
                        for i, irc in enumerate(ec_points):
                            ll = rc2ll(dem_f, dem_crs, irc)
                            epcsv.writerow(["P"+str(i), ll[0], ll[1], irc[0], irc[1]])
                        log_msg("Saving energy line to: " + ec_fn, screen_op=False)
                        return False
                    except:
                        log_msg('Saving energy line to ' + ec_fn + ' failed. Probably invalid permissions due to being locked in Excel', frame = self, errmsg = True)
                        return True


                        
                def CreateEnergyConeMesh():
                    """Creates a mesh file of the energy cone"""
                    log_msg("Preparing energy cone graphics...", frame = self)

                    px = (peakrc[1] ) * dem_cell_size
                    py = (peakrc[0] ) * dem_cell_size

                    ec_v = np.zeros_like(dem_v).astype(float)
                    ec_v.fill(np.nan)

                    min_point_rc = np.array((mesh_lr + mesh_rows//2, mesh_lc))
                    min_point_yx = min_point_rc * dem_cell_size
                    min_r = ((px - min_point_yx[1]) ** 2 + (py - min_point_yx[0]) ** 2) ** 0.5
                    min_h = -min_r * phlratio + peak_height + pincremental_height

                    #to do - Quicker with a clever numpy expression
                    
                    for i in range(mesh_lc, mesh_lc + mesh_cols):  # cols
                        for j in range(mesh_lr, mesh_lr + mesh_rows):  # rows
                            x = i * dem_cell_size
                            y = j * dem_cell_size
                            r = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
                            h = -r * phlratio + peak_height + pincremental_height

                            if h>= min_h:
                                ec_v[j,i] = h
                            else:
                                ec_v[j,i] = np.nan

                    log_msg("Saving cone graphics files...", frame = self)
                    try:
                        resolve_inout(overwrite=True) #forces overwrite of output file
                        profile = dem_f.profile
                        profile.update(dtype=rio.float32)
                        with rio.Env():
                            with rio.open(pec_graphics_fn, 'w', **profile) as dst:
                                dst.write(ec_v.astype(rio.float32), 1)
                        log_msg("Cone graphics written to: " + os.sep.join([os.getcwd(), pec_graphics_fn]), screen_op = False)
                    except:
                        log_msg('Saving energy cone in ' + pec_graphics_fn + ' failed. Probably invalid permissions due to being locked in QGIS', frame = self, errmsg = True)
                        return True
                    return False

                #########################################################################################################
                log_msg("Creating Initiation Points", screen_op = False)
                pwdir = self.pwdir
                pdem_fn = os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), self.pdem_fn])
                pthal_fn = os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), self.pthal_fn])
                papex_choice = self.papex_choice
                papex = self.papex 
                psearch_fn = self.psearch_fn
                psearch_option = self.psearch_option
                pincremental_height = self.pincremental_height
                phlratio = self.phlratio
                pplot_mesh = self.pplot_mesh
                pec_graphics_fn = os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), self.pec_graphics_fn])
                pmesh_extent = float(self.pmesh_extent)
                pinitpoints_fn = os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), self.pinitpoints_fn])
                pecline_fn = os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), self.pecline_fn])


                log_msg("Parameters", screen_op = False)
                log_msg('Parameter: pwdir; Working directory; Value: ' + pwdir, screen_op = False)
                log_msg('Parameter: pdem_fn; DEM file; Value: ' + pdem_fn, screen_op = False)
                log_msg('Parameter: pthal_fn; Stream (or thalweg) file; Value: ' + pthal_fn, screen_op = False)
                log_msg('Parameter: papex_choice; Use search file or lat/lon for apex; Value: ' + papex_choice, screen_op = False)
                log_msg('Parameter: papex; Initial entry for apex; Value: ' + str(papex), screen_op = False) # in lat long order to match input
                log_msg('Parameter: psearch_fn; Search file name; Value: ' + psearch_fn, screen_op = False) # in lat long order to match input
                log_msg('Parameter: psearch_option; Search option used; Value: ' + psearch_option, screen_op = False)
                log_msg('Parameter: pincremental_height; Incremental height on apex; Value: ' + str(pincremental_height), screen_op = False)
                log_msg('Parameter: phlratio; H/L Ratio; Value: ' + str(phlratio), screen_op = False)
                log_msg('Parameter: pplot_mesh; Flag to plot mesh; Value: ' + str(pplot_mesh), screen_op = False)
                log_msg('Parameter: pec_graphics_fn; Energy Cone Graphics file; Value: ' + pec_graphics_fn, screen_op = False)
                log_msg('Parameter: pmesh_extent; Graphics Extent; Value: ' + str(pmesh_extent), screen_op = False)
                log_msg('Parameter: pecline_fn; Energy Cone file; Value: ' + pecline_fn, screen_op = False)
                log_msg('Parameter: pinitpoints_fn; Inititation Points file; Value: ' + pinitpoints_fn, screen_op = False)

                log_msg("Loading DEM...", frame = self)
                dem_f, dem_crs, dem_v = LoadFile(pdem_fn)

                # todo 1) find a method of determing the cell size from the input file. Using the transform method is different depending on the
                # projection method. It will return meters or degrees. Currently the cell distance is just calculated from the distance between
                # two cells. This results in a slightly different value than using the transform method
                # todo 2) currently assumes cells in the matrix are square. This may not be appropriate for some project methods/tif files

                # dem_cell_size = dem_f.transform[0]
                dem_cell_size = rcdist(dem_f, dem_crs, (0, 0), (0, 1))  # distance in x direction, ie one column

                nrows = dem_v.shape[0]
                ncols = dem_v.shape[1]

                log_msg("Loading Stream file...", frame = self)
                thal_f, thal_crs, thal_v = LoadFile(pthal_fn)
                if thal_v.shape != dem_v.shape or dem_crs != thal_crs:
                    log_msg("Error - mismatch in raster size and projection between DEM file ({}) and Stream file ({})".format(self.pdem_fn, self.pthal_fn), errmsg = True, frame = self)
                    return True

                thal_v[thal_v == 65535] = 0  # set all 'NaN' values of #FFFF to zero #todo this is necessary for some outputs from GRASS r.fillnull
                thal_v[thal_v < 0] = 0  # set all negatives to zero
                thal_v[thal_v > 0] = 1  # set all stream numbers to 1

                # Find peak
                if len(args) !=0:
                    log_msg("Determining High Point...", frame = self)
                    search_sw_ll = args[0]
                    search_ne_ll = args[1]

                    try:
                        search_sw_rc = ll2rc(dem_f, dem_crs, search_sw_ll)
                        search_ne_rc = ll2rc(dem_f, dem_crs, search_ne_ll)
                    except:
                        log_msg("Error: Search area for high point is not found within the DEM file", errmsg = True, frame = self)
                        return True

                    if not (0 <= search_sw_rc[0] < nrows and 0 <= search_sw_rc[1] <= ncols and 0 <= search_ne_rc[0] < nrows and 0 <= search_ne_rc[1] <= ncols):
                        log_msg("Error: Search area for high point is not wholly within the DEM file", errmsg = True, frame = self)
                        return True

                    search_area = dem_v[search_ne_rc[0]:search_sw_rc[0] + 1, search_sw_rc[1]:search_ne_rc[1] + 1]  # area to search for highest point
                    peak_height = np.amax(search_area)  # height of highest point
                    sarearc = np.where(search_area == peak_height)  # row and column of highest point in search box
                    peakrc = np.zeros(2).astype(int)
                    peakrc[0] = sarearc[0][0] + search_ne_rc[0]  # row and column in overall table
                    peakrc[1] = sarearc[1][0] + search_sw_rc[1]
                    peakll = rc2ll(dem_f, dem_crs, peakrc)
                else:
                    peakrc = np.zeros(2).astype(int)
                    peakll = apex
                    peakrc = ll2rc(dem_f, dem_crs, peakll)
                    if not (0 <= peakrc[0] < nrows and 0 <= peakrc[1] <= ncols):
                        log_msg("Error: Apex or Centre Point is not within the DEM file", errmsg = True, frame = self)
                        return True

                    peak_height = dem_v[peakrc[0], peakrc[1]]

                # Determine Energy Cone
                log_msg("Generating Energy Cone...", frame = self)

                b = np.indices((nrows, ncols), float)
                with np.errstate(divide='ignore', invalid = 'ignore'):
                    ecraw_v = ((peak_height + pincremental_height)  - dem_v) / ((((b[0] - peakrc[0]) ** 2) + ((b[1] - peakrc[1]) ** 2)) ** .5 * dem_cell_size)
                ecraw_v[peakrc[0], peakrc[1]] = 9999
                ecraw_v = ecraw_v > phlratio

                if sys_parms['ecraw_fn'][0] !="":
                    ecraw_fn = os.sep.join([os.getcwd(), self.pwdir, sys_parms['ecraw_fn'][0]])
                    log_msg("Saving raw energy cone to: " + ecraw_fn, screen_op=False)
                    try:
                        SaveFile(ecraw_fn, dem_f, dem_crs, ecraw_v)
                    except:
                        log_msg('Saving raw energy cone in ' + ecraw_fn + ' failed. Probably invalid permissions due to being locked in QGIS', frame = self, errmsg = True)
                        return True

                log_msg("Filling Energy Cone...", frame = self)
                ecfilled_v = binary_fill_holes(ecraw_v)
                if sys_parms['ecfilled_fn'][0] !="":
                    ecfilled_fn = os.sep.join([os.getcwd(), self.pwdir, sys_parms['ecfilled_fn'][0]])
                    log_msg("Saving filled energy cone to: " + ecfilled_fn, screen_op=False)
                    try:
                        SaveFile(ecfilled_fn, dem_f, dem_crs, ecfilled_v)
                    except:
                        log_msg('Saving filled energy cone in ' + ecfilled_fn + ' failed. Probably invalid permissions due to being locked in QGIS', frame = self, errmsg = True)
                        return True

                log_msg("Generating Energy Cone Line...", frame = self)
                ecline_v = binary_erosion(input=ecfilled_v)
                ecline_v = np.logical_and(ecraw_v, np.logical_not(ecline_v))
                # remove ec line from edges as gives erroneous IPs if the cone is above the edge
                # in theory could remove a valid IP at the very edge, but this is unlikely/not an issue
                ecline_v[:, 0] = 0
                ecline_v[0, :] = 0
                ecline_v[:, ncols-1] = 0
                ecline_v[nrows-1, :] = 0
                log_msg("Saving energy line to: " + pecline_fn, screen_op=False)
                try: 
                    SaveFile(pecline_fn, dem_f, dem_crs, ecline_v)
                except:
                    log_msg('Saving energy line in ' + pecline_fn + ' failed. Probably invalid permissions due to being locked in QGIS', frame = self, errmsg = True)
                    return True

                # inititiation points
                ec_points = np.argwhere(ecline_v == 1)
                if sys_parms['ec_fn'][0] != "":
                    error = op_ec_points(ec_points, sys_parms['ec_fn'][0]) #creates csv file of ec_points for debugging
                    if error: 
                        return True

                log_msg("Generating Initiation Points...", frame = self)
                initrc = []
                ip_counter = 1
                for ii, i in enumerate(ec_points):
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
                        if i[0] < nrows-1 and i[1] < ncols-1:
                            b = [i[0] + 1, i[1]]
                            c = [i[0] + 1, i[1] + 1]
                            f = [i[0], i[1] + 1]
                            if (ecline_v[tuple(b)] == 0 and thal_v[tuple(b)] == 1 and
                                    ecline_v[tuple(c)] == 1 and thal_v[tuple(c)] == 0 and
                                    ecline_v[tuple(f)] == 0 and thal_v[tuple(f)] == 1):
                                initrc.append([ip_counter, b[0], b[1]])
                                log_msg("Adding extra ip: " + str(ip_counter), screen_op = False)
                                ip_counter += 1
                                ip_found = True
                        # se direction
                        if i[0] > 0 and i[1] < ncols-1 and not ip_found:
                            f = [i[0], i[1] + 1]
                            h = [i[0] - 1, i[1]]
                            j = [i[0] - 1, i[1] + 1]
                            if (ecline_v[tuple(f)] == 0 and thal_v[tuple(f)] == 1 and
                                    ecline_v[tuple(h)] == 0 and thal_v[tuple(h)] == 1 and
                                    ecline_v[tuple(j)] == 1 and thal_v[tuple(j)] == 0):
                                initrc.append([ip_counter, f[0], f[1]])
                                log_msg("Adding extra ip: " + str(ip_counter), screen_op = False)
                                ip_counter += 1
                                ip_found = True
                if len(initrc) == 0:
                    log_msg("No initiation points found...", frame = self)
                else:
                    initrc = np.array(initrc)

                    # Save initiation points in geopackage format
                    log_msg("Saving initiation points to " + pinitpoints_fn, frame = self)
                    geoms = [shPoint((peakll[0], peakll[1]))]
                    index = ["Apex"]
                    for i, irc in enumerate(initrc):
                            ll = rc2ll(dem_f, dem_crs, irc[1:3])
                            geoms.append(shPoint((ll[0], ll[1])))
                            index.append("IP{:02d}".format(irc[0]))
                    gds = gpd.GeoSeries(geoms, index, crs="EPSG:4326")
                    gds.to_file(pinitpoints_fn, driver="GPKG", mode = 'w') #fff

                    # Initiation points and peak saved in a csv file if desired. 
                    # Option only avail in programme. Not intended for normal user. 
                    # This can be edited and reloaded

                    if sys_parms['wipcsv'][0] != "":
                        #assumes filename has csv extension. Not verified
                        pwipcsv = os.sep.join([os.getcwd(), self.pwdir, sys_parms['wipcsv'][0]])
                        log_msg("Saving initiation points additionally to: " + pwipcsv, screen_op = False)
                        try:
                            f_initpoints = open(pwipcsv, "w", newline = '')
                            ipcsv = csv.writer(f_initpoints, delimiter=',', dialect="excel", quoting=csv.QUOTE_MINIMAL)
                            ipcsv.writerow(["Label", "Longitude", "Latitude", "Number", "Row", "Column"])
                            ipcsv.writerow(["Apex", peakll[0], peakll[1], "", peakrc[0], peakrc[1]])

                            for i, irc in enumerate(initrc):
                                ll = rc2ll(dem_f, dem_crs, irc[1:3])  # this programme uses long, lat to match x,y directions. Presented as Lat, Long in all output
                                ipcsv.writerow(["IP{:02d}".format(irc[0]), ll[0], ll[1], irc[0], irc[1], irc[2]])
                        except:
                            log_msg('Saving initiation points to ' + pwipcsv + ' failed. Probably invalid permissions due to being locked in Excel', frame = self, errmsg = True)
                            return True

                if pplot_mesh:

                    # determine the parameters to use for the size of the mesh files
                    if np.size(initrc) == 0:
                        mesh_rows = nrows
                        mesh_cols = ncols
                        mesh_lr = 0
                        mesh_lc = 0
                    else:
                        mesh_rows_m2 = int(np.amax(abs(initrc[:, 1] - peakrc[0])) * pmesh_extent)
                        mesh_cols_m2 = int(np.amax(abs(initrc[:, 2] - peakrc[1])) * pmesh_extent)
                        mesh_m2 = max(mesh_rows_m2, mesh_cols_m2)

                        mesh_lr = max(peakrc[0] - mesh_m2, 0)
                        mesh_lc = max(peakrc[1] - mesh_m2, 0)
                        mesh_ur = min(peakrc[0] + mesh_m2, nrows-1)
                        mesh_uc = min(peakrc[1] + mesh_m2, ncols-1)

                        mesh_rows = mesh_ur - mesh_lr + 1
                        mesh_cols = mesh_uc - mesh_lc + 1

                    error = CreateEnergyConeMesh()
                    if error:
                        return True
                if len(initrc) == 0:
                    log_msg('No initiation points found. Energy cone graphic will have been created if requested.', frame = self, errmsg = True)
                    return True
                return False

            #############################################################################################                    

            #determine apex of energey cone
            if self.papex_choice == "LatLon":
                error = create_ips(self.papex)
                return error

            else: #Search
                s_fnp = os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), self.psearch_fn])
                s_f = gpd.GeoDataFrame.from_file(s_fnp)
                psearch_option = self.tk_psearch_option.get()

                if psearch_option == "Highest Point":
                    found = False
                    i = 0
                    while i < len(s_f['index']) and not found:
                        if s_f['index'][i] == "Search Area" and not s_f.isna()['geometry'][i]:
                            found = True
                        else:
                            i += 1
                    if found:
                        bounds = s_f['geometry'][i].bounds # minx, miny, maxx, maxy
                        error = create_ips([mean([bounds[0], bounds[2]]), mean([bounds[1], bounds[3]])], bounds[0:2], bounds[2:4]) #centre x, centre y, sw, ne
                        return error
                    else:
                        log_msg("Error: Search Area not found in search file " + self.psearch_fn, frame = self, errmsg = True)
                        return True


                elif psearch_option == "Centre":
                    found = False
                    i = 0
                    while i < len(s_f['index']) and not found:
                        if s_f['index'][i] == "Search Area" and not s_f.isna()['geometry'][i]:
                            found = True
                        else:
                            i += 1
                    if found:
                        bounds = s_f['geometry'][i].bounds
                        error = create_ips([mean([bounds[0], bounds[2]]), mean([bounds[1], bounds[3]])])
                        return error
                    else:
                        log_msg("Error: Search Area not found in search file " + self.psearch_fn, frame = self, errmsg = True)
                        return True

                elif psearch_option == "Centre Point":
                    found = False
                    i = 0
                    while i < len(s_f['index']) and not found:
                        if s_f['index'][i] == "Centre" and not s_f.isna()['geometry'][i]:
                            found = True
                        else:
                            i += 1
                    if found:
                        error = create_ips([s_f['geometry'][i].x, s_f['geometry'][i].y ])
                        return error
                    else:
                        log_msg("Error: Centre point not found in search file " + self.psearch_fn, frame = self, errmsg = True)
                        return True
                return False

        self.frame = create_frame()
        load_parameters()
        title(10)
        DEM_file(20)
        thal_file(25)
        apex_choice(30)
        self.papex_choice = self.tk_papex_choice.get()
        if self.papex_choice == "Search":
            overwrite_message1(45)
            search_file(50)
            new_sf_button(55)
            search_option(70)
        elif self.papex_choice == "LatLon":
            get_apex(40)
        incremental_height(80)
        hlratio(90)
        plot_mesh(100)
        if self.pplot_mesh:
            overwrite_message2(100)
            ec_graphics_fn(105)
            mesh_extent(115)
        else:
            overwrite_message2(103)

        ecline_file(118)
        initpoints_file(120)
        ip_button(200)
        back_button(200)
        status_msg(220)

    def exec_frame3(self):

        def create_frame():
            # Create a frame on the canvas to contain the widgets
            frame = tk.Frame(self.canvas)
            frame.columnconfigure((0,1,2,3), weight = 1)
            frame.rowconfigure(0, weight = 1)
            frame.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = tk.NW)
            frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
            self.canvas.create_window((0, 0), window=frame, anchor="nw")
            self.canvas.yview_moveto('0')

            return frame

        def title(r):
            # title
            tk.Label(self.frame, text='Generate Flows', font=('Helvetica', 14, 'bold')).grid(row=r, column = 0, padx = 10, columnspan=1, sticky='NW')
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r+1, column = 0, padx = 10, columnspan=1, sticky='NW')

        def DEM_file(r):
            tk.Label(self.frame, text='DEM File', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pdem_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pdem_fn.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pdem_fn.insert(0, self.pdem_fn)
            self.tk_pdem_fn_msg = tk.Label(self.frame, text='Name of your DEM file in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pdem_fn_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def thal_file(r):
            tk.Label(self.frame, text='Streams File', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pthal_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pthal_fn.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pthal_fn.insert(0, self.pthal_fn)
            self.tk_pthal_fn['state']= 'disabled'
            self.tk_pthal_fn_msg = tk.Label(self.frame, text='Name of your streams file in ' + self.pwdir + ' (not used to generate lahars)', font=('Helvetica', 12))
            self.tk_pthal_fn_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')


        def flow_file(r):
            tk.Label(self.frame, text='Flow Direction File', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pflow_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pflow_fn.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pflow_fn.insert(0, self.pflow_fn)
            self.tk_pflow_fn_msg = tk.Label(self.frame, text='Name of your flow direction file in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pflow_fn_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r+1, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')

        def initpoints_file(r):
            self.tk_pinitpoints_fn_lbl =  tk.Label(self.frame, text='Initiation Points File', font=('Helvetica', 12))
            self.tk_pinitpoints_fn_lbl.grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pinitpoints_fn = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pinitpoints_fn.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pinitpoints_fn.insert(0, self.pinitpoints_fn)
            self.tk_pinitpoints_fn_msg = tk.Label(self.frame, text='Name of the file with the initiations points in ' + self.pwdir, font=('Helvetica', 12))
            self.tk_pinitpoints_fn_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text = '' , font=('Helvetica', 12)).grid(row=r+1, column=0, padx = 10, pady = 3, columnspan=1, sticky='W')

        def volume(r):
            tk.Label(self.frame, text='Volume(s)', font=('Helvetica', 12)).grid(row=r, column=0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pvolume = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pvolume.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pvolume.insert(0, self.pvolume)
            self.tk_pvolume_msg = tk.Label(self.frame, text='Volumes (m^3) in a list separated by commas ', font=('Helvetica', 12))
            self.tk_pvolume_msg.grid(row=r, column=3, padx = 10, pady = 3, columnspan=4, sticky='W')

        def scenario(r):
            tk.Label(self.frame, text='Scenario', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pscenario = ttk.Combobox(self.frame, font=('Helvetica', 12), state = 'readonly', values = sys_parms['pscenario_values'][0])
            self.tk_pscenario.current(sys_parms['pscenario_values'][0].index(self.pscenario))
            self.tk_pscenario.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pscenario_msg = tk.Label(self.frame, text='Name of the scenario to use', font=('Helvetica', 12))
            self.tk_pscenario_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pscenario.bind("<<ComboboxSelected>>", select_scenario)

        def select_scenario(eventObject):
            self.pscenario = self.tk_pscenario.get()
            format_c1()
            format_c2()

        def format_c1():
            if self.pscenario != 'Custom':
                i = sys_parms['pscenario_values'][0].index(self.pscenario)
                self.pc1_value = sys_parms['pc1_values'][0][i]
                self.tk_pc1_value['state'] = 'normal'
                self.tk_pc1_value.delete(0, "end")
                self.tk_pc1_value.insert(0, self.pc1_value)
                self.tk_pc1_value['state'] = 'disabled'
            else:
                self.tk_pc1_value['state'] = 'normal'
                self.tk_pc1_value.delete(0, "end")
                self.tk_pc1_value.insert(0, self.pc1_value)
                
        def format_c2():
            if self.pscenario != 'Custom':
                i = sys_parms['pscenario_values'][0].index(self.pscenario)
                self.pc2_value = sys_parms['pc2_values'][0][i]
                self.tk_pc2_value['state'] = 'normal'
                self.tk_pc2_value.delete(0, "end")
                self.tk_pc2_value.insert(0, self.pc2_value)
                self.tk_pc2_value['state'] = 'disabled'
            else:
                self.tk_pc2_value['state'] = 'normal'
                self.tk_pc2_value.delete(0, "end")
                self.tk_pc2_value.insert(0, self.pc2_value)


        def c1_value(r):
            tk.Label(self.frame, text='Cross sectional area:', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text='c\u2081', font=('Helvetica', 16)).grid(row=r, column = 1, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pc1_value = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pc1_value.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            format_c1()
            self.tk_pc1_value_msg = tk.Label(self.frame, text='Value of the c1 parameter', font=('Helvetica', 12))
            self.tk_pc1_value_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def c2_value(r):
            tk.Label(self.frame, text='Planar Area', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text='c\u2082', font=('Helvetica', 16)).grid(row=r, column = 1, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_pc2_value = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_pc2_value.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            format_c2()
            self.tk_pc2_value_msg = tk.Label(self.frame, text='Value of the c2 parameter', font=('Helvetica', 12))
            self.tk_pc2_value_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')

        def display_formula(r):
            tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text='Formula', font=('Helvetica', 12)).grid(row=r+1, column = 0, padx = 10, pady = 3, columnspan=1, sticky = 'W')
            tk.Label(self.frame, text='Cross Sectional Area =', font=('Helvetica', 12)).grid(row=r+1, column = 0, padx = 10, pady = 3, columnspan=1, sticky = 'W')
            tk.Label(self.frame, text='c\u2081 V\u00B2\u141F\u00B3', font=('Helvetica', 16)).grid(row=r+1, column = 1, padx = 10, pady = 3, columnspan=2, sticky = 'W')
            tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=r+2, column = 0, padx = 10, pady = 3, columnspan=2, sticky='W')
            tk.Label(self.frame, text='Planar Area =', font=('Helvetica', 12)).grid(row=r+2, column = 0, padx = 10, pady = 3, columnspan=1, sticky = 'W')
            tk.Label(self.frame, text='c\u2082 V\u00B2\u141F\u00B3', font=('Helvetica', 16)).grid(row=r+2, column = 1, padx = 10, pady = 3, columnspan=2, sticky = 'W')
            tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=r+3, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
           
        def sea_level(r):
            tk.Label(self.frame, text='Sea Level', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_psea_level = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_psea_level.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_psea_level.insert(0, self.psea_level)
            self.tk_psea_level_msg = tk.Label(self.frame, text='Flow will stop at sea level', font=('Helvetica', 12))
            self.tk_psea_level_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text='', font=('Helvetica', 12)).grid(row=r+1, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')

        def lahar_dir(r):
            tk.Label(self.frame, text = 'Uncheck box to disable overwite check', font=('Helvetica', 10, 'italic')).grid(row=r-1, column = 1, padx = 10, columnspan=2, sticky='W')
            self.tk_plahar_dir_lbl = tk.Label(self.frame, text='Flow Output Directory', font=('Helvetica', 12))
            self.tk_plahar_dir_lbl.grid(row=r, column = 0, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_ld_ow = tk.BooleanVar(value = self.pld_ow)
            self.tk_ld_ow_chk = tk.Checkbutton(self.frame, text='', font=('Helvetica', 12), variable=self.tk_ld_ow).grid(row=r, column = 1, padx = 10, columnspan=1, sticky='W')

            self.tk_plahar_dir = tk.Entry(self.frame, font=('Helvetica', 12))
            self.tk_plahar_dir.grid(row=r, column = 2, padx = 10, pady = 3, columnspan=1, sticky='W')
            self.tk_plahar_dir.insert(0, self.plahar_dir)
            self.tk_plahar_dir_msg = tk.Label(self.frame, text='Directory for flow output files',font=('Helvetica', 12))
            self.tk_plahar_dir_msg.grid(row=r, column = 3, padx = 10, pady = 3, columnspan=1, sticky='W')
            tk.Label(self.frame, text = '' , font=('Helvetica', 12)).grid(row=r+1, column=0, padx = 10, pady = 3, columnspan=1, sticky='W')

        def validate_DEM():
            self.pdem_fn = self.tk_pdem_fn.get()
            self.pdem_fn, error, self.tk_pdem_fn_msg['text'] = validate_file_to_read(self.pdem_fn, self.pwdir, type = 'tif')
            self.tk_pdem_fn.delete(0, "end") #update file name on screen post validation
            self.tk_pdem_fn.insert(0, self.pdem_fn)

            if error:
                self.tk_pdem_fn_msg['fg'] = 'red'
            return error

        def validate_thal():
            #no validation
            self.tk_pthal_fn_msg['text'] = ""
            return False

        def validate_scenario():
            #no validation
            self.tk_pscenario_msg['text'] = ""
            return False

        def validate_flow():
            self.pflow_fn = self.tk_pflow_fn.get()
            self.pflow_fn,error, self.tk_pflow_fn_msg['text'] = validate_file_to_read(self.pflow_fn, self.pwdir, type = 'tif')
            self.tk_pflow_fn.delete(0, "end") #update file name on screen post validation
            self.tk_pflow_fn.insert(0, self.pflow_fn)

            if error:
                self.tk_pflow_fn_msg['fg'] = 'red'
            return error

        def validate_initiationpoints():
            self.pinitpoints_fn = self.tk_pinitpoints_fn.get()
            self.pinitpoints_fn, error, self.tk_pinitpoints_fn_msg['text'] = validate_file_to_read(self.pinitpoints_fn, self.pwdir, type = 'gpkg')
            self.tk_pinitpoints_fn.delete(0, "end") #update file name on screen post validation
            self.tk_pinitpoints_fn.insert(0, self.pinitpoints_fn)

            if error:
                self.tk_pinitpoints_fn_msg['fg'] = 'red'
            return error
        
        def validate_volume():
            self.pvolume_value = self.tk_pvolume.get().split(",")
            error = False
            i = 0
            while i < len(self.pvolume_value) and not error:
                self.pvolume_value[i], error, self.tk_pvolume_msg['text'] = validate_numeric(self.pvolume_value[i])
                i += 1
            if error:
                self.tk_pvolume_msg['fg'] = 'red'
            else:
                self.pvolume_value.sort()
                self.pvolume = ', '.join("{:.2e}".format(x) for x in self.pvolume_value) #converts list to csv string
                self.tk_pvolume.delete(0, "end")
                self.tk_pvolume.insert(0, self.pvolume)

            return error

        def validate_c1():
            self.tk_pc1_value_msg['text'] = ""

            self.pc1_value = self.tk_pc1_value.get()
            self.pc1_value, error, self.tk_pc1_value_msg['text'] = validate_numeric(self.pc1_value, zero = True)

            if error:
                self.tk_pc1_value_msg['fg'] = "red"
            return error

        def validate_c2():
            self.tk_pc2_value_msg['text'] = ""

            self.pc2_value = self.tk_pc2_value.get()
            self.pc2_value, error, self.tk_pc2_value_msg['text'] = validate_numeric(self.pc2_value, zero = True)

            if error:
                self.tk_pc2_value_msg['fg'] = "red"
            return error


        def validate_sea_level():
            self.tk_psea_level_msg['text'] = ""

            self.psea_level = self.tk_psea_level.get()
            self.psea_level, error, self.tk_psea_level_msg['text'] = validate_numeric(self.psea_level, zero = True)

            if error:
                self.tk_psea_level_msg['fg'] = "red"

            return error
        
        def validate_lahar_dir():
            self.tk_plahar_dir_msg['text'] = ""
            self.pld_ow = self.tk_ld_ow.get()
            self.plahar_dir = self.tk_plahar_dir.get()
            self.plahar_dir, error, cancel_flag, self.tk_plahar_dir_msg['text'] = validate_dir_to_write(self.plahar_dir, self.pwdir, self.frame, "Lahar Directory", exists = self.pld_ow)
            self.tk_plahar_dir.delete(0, "end") #update file name on screen post validation
            self.tk_plahar_dir.insert(0, self.plahar_dir)

            if error:
                self.tk_plahar_dir_msg['fg'] = "red"
            return error, cancel_flag

        def back_button(r):
            self.tk_back_button = tk.Button(self.frame, text='Back', font=('Helvetica', 12))
            self.tk_back_button.grid(row=r, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_back_button['command'] = press_back_button

        def lahar_button(r):
            self.tk_lahar_button = tk.Button(self.frame, text='Create Flows', font=('Helvetica', 12))
            self.tk_lahar_button.grid(row=r, column = 2, padx = 10, columnspan=1, sticky='W')
            self.tk_lahar_button['command'] = press_lahar_button

        def lh_conf_window():
                # freeze frame
                freeze_list = []
                for child in self.frame.winfo_children():
                        freeze_list.append([child, child.cget('state')])
                        child.configure(state='disabled')

                # create pop out from frame
                po_toplvl = tk.Toplevel()
                po_toplvl.columnconfigure(0, weight = 1)
                po_toplvl.rowconfigure(0, weight = 1)
                po_toplvl['borderwidth'] = 50

                frame1 = tk.Frame(po_toplvl)
                frame1.columnconfigure(0, weight = 1)
                frame1.rowconfigure(0, weight = 1)
                frame1.grid(row = 0, column = 0, padx = 10, sticky=tk.NSEW)
                pscenario = self.tk_pscenario.get()

                tk.Label(frame1, text=pscenario + " Flows created", font=('Helvetica', 12, 'bold')).grid(row=10, column = 0, padx = 10, columnspan=2, sticky='W')

                tk_proceed_button = tk.Button(frame1, text="Continue", font=('Helvetica', 12), command = lambda : proceed.set(True))
                tk_proceed_button.grid(row=30, column = 0, padx = 10, pady = 20, columnspan=1)

                #pause execution until button is pressed
                proceed = tk.BooleanVar()
                proceed.set(False)
                tk_proceed_button.wait_variable(proceed)

                #unfreeze frame
                for i in freeze_list:
                        i[0].configure(state=i[1])
                #remove pop up
                po_toplvl.destroy()

        def status_msg(r):
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r, column = 0, padx = 10, columnspan=1, sticky='NW')
            self.tk_statusmsg = tk.Label(self.frame, text = "", font=('Helvetica', 12))
            self.tk_statusmsg.grid(row=r+1, column = 0, columnspan=4, sticky='W')

        def press_back_button():
            self.frame.destroy()
            self.exec_frame1()

        def press_lahar_button():
            self.tk_statusmsg["text"] = ""
            error = True in {validate_DEM(), validate_flow(), validate_initiationpoints(), validate_scenario(), validate_volume(), validate_sea_level(), validate_thal()}
            if self.pscenario == 'Custom':
                error = True in {error, validate_c1(), validate_c2()}
            
            e, cf = validate_lahar_dir()
            error = error or e

            if error:
                self.tk_statusmsg["text"] = "Please correct errors before continuing"
                self.tk_statusmsg['fg'] = "red"
            else:
                if not cf:
                    save_parameters()
                    error = gen_lahars()
                    if not error: 
                        lh_conf_window()
                        self.frame.destroy()
                        self.exec_frame1() #start
            return

        def save_parameters():
            self.parameters['pdem_fn'] = self.pdem_fn
            self.parameters['pthal_fn'] = self.pthal_fn
            self.parameters['pflow_fn'] = self.pflow_fn
            self.parameters['pinitpoints_fn'] = self.pinitpoints_fn
            self.parameters['pvolume'] = self.pvolume

            self.parameters['pscenario'] = self.tk_pscenario.get()
            self.parameters['pc1_value'] = self.pc1_value
            self.parameters['pc2_value'] = self.pc2_value
            self.parameters['psea_level'] = self.psea_level
            self.parameters['plahar_dir'] = self.plahar_dir
            self.parameters['pld_ow'] = self.pld_ow
            pickle.dump(self.parameters, open(os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), "parameters.pickle"]), "wb"))

        def load_parameters():
            # Load Parameters
            try:
                self.parameters = pickle.load(open(os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), "parameters.pickle"]), "rb"))
            except:
                self.parameters = {}
            
            try:
                self.pdem_fn = self.parameters['pdem_fn']
                self.pinitpoints_fn = self.parameters['pinitpoints_fn']
                self.pthal_fn = self.parameters['pthal_fn']
            except:
                self.pdem_fn = ""
                self.pthal_fn = ""
                self.pinitpoints_fn = ""

            try:
                self.pflow_fn = self.parameters['pflow_fn']
                self.pvolume = self.parameters['pvolume']
                self.pscenario = self.parameters['pscenario']
                if self.pscenario not in sys_parms['pscenario_values'][0]:
                    self.pscenario = "Lahar"
                self.pc1_value = self.parameters['pc1_value']
                self.pc2_value = self.parameters['pc2_value']
                self.psea_level = self.parameters['psea_level']
                self.plahar_dir = self.parameters['plahar_dir']
                self.pld_ow = self.parameters['pld_ow']

            except:
                self.pflow_fn = ""
                self.pvolume = ""
                self.pscenario = "Lahar"
                self.pc1_value = "0.05"
                self.pc2_value = "200"
                self.psea_level = "0"
                self.plahar_dir = "lahars"
                self.pld_ow = True
            
        def gen_lahars():
            class lhpoint(object):
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
                            log_msg("Warning: potential overflow as {} is added to row {}".format(r2, r1), screen_op=False)
                        if c1 + c2 > ncols - 1 or c1 + c2 < 0:
                            log_msg("Warning: potential overflow as {} is added to column {}".format(c2, c1), screen_op=False)
                    else:
                        r3 = r1 + r2
                        c3 = c1 + c2
                    return lhpoint([r3, c3])

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
                            log_msg("Warning: potential overflow as {} is subtracted from row {}".format(r2, r1), screen_op=False)
                        if c1 - c2 > ncols - 1 or c1 - c2 < 0:
                            log_msg("Warning: potential overflow as {} is subtracted from column {}".format(c2, c1), screen_op=False)
                    else:
                        r3 = r1 - r2
                        c3 = c1 - c2
                    return lhpoint([r3, c3])

                def vector(self):
                    """returns a list of the components of the point to allow it to be used for indexing numpy arrays"""
                    return (self.p[0], self.p[1])

                def __eq__(self, other):
                    if not isinstance(other, lhpoint):
                        # don't attempt to compare against unrelated types
                        return NotImplemented
                    return self.p == other.p

            def gen_lahar(v, ip):
                def EvalPoint(pathpoint, plan_area):
                    """Evaluates a point on the lahar"""
                    # increments the lahar level from the elevation of the channel point being considered until the cross sectional area
                    # limit is met. Does this four times - ie in each of the following directions: N-S, E-W, NW-SE and SW-NE. Cross
                    # sectional area is the sum of the area in all four directions.

                    # def Plot_xsecarea(ppos, pneg, pathpoint, level, direction, seq, innund):
                    def Plot_xsecarea(p_pos, p_neg):
                        """"Plots an image of the cross sectional area of the Lahar at a particular point in a particular direction"""
                        # Mostly usefule for debugging but supports a bit more in depth analysis of a peculiar point on a lahar
                        
                        
                        def PlotMsg(msg, x, y, anchor="tl", fill="#000000"):
                            """Plots text on the Cross Section Chart"""
                            # anchor
                            # t - top, m - middle, b - bottom
                            # l = left, c = centre, r = right
                            wl, wt, wr, wb = font.getbbox(msg)
                            wt, ht = wr-wl, wb-wt

                            if anchor[0] == 't':
                                ht = 0
                            elif anchor[0] == "m":
                                ht = ht / 2
                            elif anchor[0] == 'a': #above
                                ht = y - ht - 1
                            elif anchor[0] == 'b': #above
                                ht = ht

                            if anchor[1] == 'l':
                                wt = 0
                            elif anchor[1] == "c":
                                wt = wt / 2
                            draw1.text((x - wt, y - ht), msg, fill=fill, font=font)

                        
                        global draw1
                        global font

                        xsecarea = 0

                        # plot from 2 cells to the 'positive' and two cells to the 'negative'
                        if direction == "N-S":
                            inc = lhpoint([1, 0])
                            dist = dem_cell_size
                        elif direction == "W-E":
                            inc = lhpoint([0, 1])
                            dist = dem_cell_size
                        elif direction == "SW-NE":
                            inc = lhpoint([1, 1])
                            dist = dem_cell_size * 2 ** 0.5
                        elif direction == "NW-SE":
                            inc = lhpoint([-1, 1])
                            dist = dem_cell_size * 2 ** 0.5

                        p_neg = p_neg.minus(inc, "N")
                        p_neg = p_neg.minus(inc, "N")
                        p_pos = p_pos.plus(inc, "N")
                        p_pos = p_pos.plus(inc, "N")

                        # get number of cells
                        rl = abs(p_pos.vector()[0] - p_neg.vector()[0]) + 1  # number of point along a row
                        cl = abs(p_pos.vector()[1] - p_neg.vector()[1]) + 1  # number of points along a column
                        ncells = max(rl, cl)

                        # get bottom of channel
                        chan_base = dem_v[pathpoint.vector()]
                        pgborder = 50
                        maxh = dem_v[pathpoint.vector()]
                        minh = dem_v[pathpoint.vector()]

                        p = p_neg
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

                        p = p_neg
                        for i in range(ncells):
                            # draw ground
                            xnw = int(i * ww) + pborder
                            xse = int((i + 1) * ww) - 1 + pborder
                            yse = pheight - pborder
                            ynw = pheight - (int((dem_v[p.vector()] - minh) * hh) + pgborder + pborder)
                            draw1.rectangle([(xnw, ynw), (xse, yse)], fill='#548235')
                            draw1.line([(xse, yse), (xnw, yse), (xnw, ynw), (xse, ynw), xse, yse], fill='#000000')

                            PlotMsg("R:{} C:{}".format(p.vector()[0], p.vector()[1]), (xse + xnw) / 2, yse + 1, "tc", "#FFFFFF")
                            PlotMsg("Elev:{:.2f}".format(dem_v[p.vector()]), (xse + xnw) / 2, ynw + 1, "tc", "#FFFFFF")

                            # draw lahar
                            if innund[p.vector()] and i in range(2, ncells - 2):
                                xsecarea += (level - dem_v[p.vector()]) * dist
                                # xnw = int(i * ww) + pborder
                                # xse = int((i + 1) * ww) - 1 + pborder
                                yse = pheight - (int((dem_v[p.vector()] - minh) * hh) + pgborder + pborder)
                                ynw = pheight - (int((level - minh) * hh) + pgborder + pborder)
                                draw1.rectangle([(xnw, ynw), (xse, yse)], fill='#8C3838')
                                draw1.line([(xse, yse), (xnw, yse), (xnw, ynw), (xse, ynw), (xse, yse)], fill='#000000')
                                lf = True

                            # draw sky - assumes cordinates from either ground or lahar
                            yse = ynw + 1
                            ynw = pheight - (pheight - pborder)
                            draw1.rectangle([(xnw, ynw), (xse, yse)], fill='#7DF5FB')
                            draw1.line([(xse, yse), (xnw, yse), (xnw, ynw), (xse, ynw), (xse, yse)], fill='#000000')
                            if p == pathpoint and lf:
                                PlotMsg("Level:{:.2f}".format(level), (xnw + xse) / 2, yse-4, "bc", "#000000")

                            p = p.plus(inc, "N")

                        PlotMsg("Cross Sectional Area Calculated: {:.2f} Cross Sectional Area Limit: {:.2f} Cell width: {:.2f}".format(xsecarea, xsec_area_limit, dist), pborder, pheight - (pheight - 10), "tl",
                                "#FFFFFF")
                        fn = "Point P{} R{}-C{}-{}".format(seq, pathpoint.vector()[0], pathpoint.vector()[1], direction)
                        log_msg("Cross sectional graphic created for Point P{} R{}-C{}-{}".format(seq, pathpoint.vector()[0], pathpoint.vector()[1], direction), frame = self)
                        img.save(os.sep.join([pcrosssec_area_dir, fn + '.png']))
                        img.close
                    
                    innund[pathpoint.vector()] = 1
                    directions = ["N-S", "W-E", "NW-SE", "SW-NE"]

                    for direction in directions:
                        # cycle through each direction. Sets a vector to move in a positive direction and a negative direction away from the
                        # initial point. Positive and negative are arbitrary terms to describe the opposite directions. If direction is
                        # diagonal then each step has a distance of root 2.
                        # Cross sectional areas where the profile is in the direction of the stream are ignored
                        #
                        # If the calculation of the cross sectional area over tops a local maximum, the area of the downstream section is
                        # not considered. This doesn't seem to be a case considered in Schilling
                        #
                        # The class lhPoint is used as the plus and minus operators prevent overflow if the cross sectional area is close to
                        # the boundary. In this case the positive or negitive point remains on the boundary as the level increases.
                        # To be technically correct, a larger DEM should be used to allow the cross sectional area and innundation to
                        # be completed. A warning is printed in the Plus or Minus operations in the class.

                        if direction != ignore:
                            if direction == "N-S":
                                pos_vect = lhpoint([1, 0])
                                neg_vect = lhpoint([-1, 0])
                                inc_dist = dem_cell_size
                            elif direction == "W-E":
                                pos_vect = lhpoint([0, 1])
                                neg_vect = lhpoint([0, -1])
                                inc_dist = dem_cell_size
                            elif direction == "NW-SE":
                                pos_vect = lhpoint([-1, 1])
                                neg_vect = lhpoint([1, -1])
                                inc_dist = 2 ** 0.5 * dem_cell_size
                            elif direction == "SW-NE":
                                pos_vect = lhpoint([1, 1])
                                neg_vect = lhpoint([-1, -1])
                                inc_dist = 2 ** 0.5 * dem_cell_size

                            dy = sys_parms['dy'][0]
                            dist = inc_dist
                            xsec_area = inc_dist * dy
                            level = dem_v[pathpoint.vector()] + dy  # initial level of flow
                            p_pos = pathpoint  # set both points to the initial path point
                            p_neg = pathpoint  # set both points to the initial path point

                            while xsec_area <= xsec_area_limit and plan_area <= plan_area_limit:
                                raise_level = True
                                p_pos_new = p_pos.plus(pos_vect)
                                p_pos_new_level = dem_v[p_pos_new.vector()]
                                if level > p_pos_new_level and p_pos_new_level > self.psea_level:
                                    p_pos = p_pos_new
                                    dist += inc_dist
                                    xsec_area += inc_dist * (level - dem_v[p_pos.vector()])
                                    innund[p_pos.vector()] = 1
                                    plan_area += dem_cell_size ** 2
                                    raise_level = False

                                if xsec_area <= xsec_area_limit:
                                    p_neg_new = p_neg.plus(neg_vect)
                                    p_neg_new_level = dem_v[p_neg_new.vector()]
                                    if level > p_neg_new_level and p_neg_new_level > self.psea_level:
                                        p_neg = p_neg_new
                                        dist += inc_dist
                                        xsec_area += inc_dist * (level - dem_v[p_neg.vector()])
                                        innund[p_neg.vector()] = 1
                                        plan_area += dem_cell_size ** 2
                                        raise_level = False

                                if raise_level and xsec_area <= xsec_area_limit:
                                    level += dy
                                    xsec_area += dist * dy

                            if sys_parms['pplotxsecarea'][0] and ip[0] == sys_parms['pplotip'][0] and v == sys_parms['pplotvol'][0]:
                                # Plot_xsecarea(p_pos, p_neg, pathpoint, level, i, seq, innund)
                                Plot_xsecarea(p_pos, p_neg)
                    return plan_area, innund

                ###################################################################################################
                """Generates the lahar for a particular volume and initiation point"""
                xsec_area_limit = float(self.pc1_value) * v ** (2 / 3)  # Cross sectional area in m2
                plan_area_limit = float(self.pc2_value) * v ** (2 / 3)  # Planimetric area in m2
                dy = 1  # Increment of elevation in m

                plotcsv = False
                if sys_parms['pplotxsecarea'][0] and ip[0] == sys_parms['pplotip'][0] \
                    and v == sys_parms['pplotvol'][0] and sys_parms['pxsec_fn'][0] != "":
                    plotcsv = True
                    xseccsv = csv.writer(open(os.sep.join([pcrosssec_area_dir, sys_parms['pxsec_fn'][0]]), "w", newline = ""), delimiter=',', quoting=csv.QUOTE_ALL)
                    xseccsv.writerow(["Point", "Latitude", "Longitude", "Row", "Col"])

                innund = np.zeros_like(dem_v).astype(int)  # Defines a zeros rasters where the inundation cells will be writen as 1's values.
                plan_area = 0

                # cycle down the stream until the planometric area limit is exceeded
                # Stops when it reaches the sea
                ## Channel paths terminate 1 cell from the
                ## map edge so no danger of overflow.
                current_point = lhpoint([ip[1], ip[2]])
                point_number = 1
                flow_direction = flowdir_v[current_point.vector()]  # 1 = NE, 2 = N, 3 = NW...continuing ACW until 8 = E. Some minus error values can exist on the edges

                while plan_area <= plan_area_limit and dem_v[current_point.vector()] > self.psea_level and flow_direction > 0:

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
                            "Possibly this is because the point is at the very edge of the DEM. Terminating".format(current_point.vector(), flow_direction), screen_op = False)
                        sys.exit()

                    if plotcsv:
                        ipll = rc2ll(dem_f, dem_crs, (current_point.vector()[0], current_point.vector()[1]))
                        xseccsv.writerow(["P{:02d}".format(point_number), ipll[1], ipll[0], current_point.vector()[0], current_point.vector()[1]])

                    seq = str(point_number)
                    plan_area, innund = EvalPoint(current_point, plan_area)

                    # also evaluate adjacent point if flowing in a diagonal
                    # if flowing NW, evaluate 1 point left (West)
                    if flow_direction == 3 and dem_v[current_point.plus(lhpoint([0, -1])).vector()] > self.psea_level:
                        seq += "+W"
                        plan_area, innund = EvalPoint(current_point.plus(lhpoint([0, -1])), plan_area)
                        if plotcsv:
                            ipll = rc2ll(dem_f, dem_crs, (current_point.plus(lhpoint([0, -1])).vector()))
                            xseccsv.writerow(["P{:02d}W".format(point_number), ipll[1], ipll[0], current_point.plus(lhpoint([0, -1])).vector()[0], current_point.plus(lhpoint([0, -1])).vector()[1]])
                    # if flowing SW, evaluate 1 point below (South) - note that the DEM is inverted hence the vector for south is 1,0 rather than -1,0
                    elif flow_direction == 5 and dem_v[current_point.plus(lhpoint([1, 0])).vector()] > self.psea_level:
                        seq += "+S"
                        plan_area, innund = EvalPoint(current_point.plus(lhpoint([1, 0])), plan_area)
                        if plotcsv:
                            ipll = rc2ll(dem_f, dem_crs, (current_point.plus(lhpoint([1, 0])).vector()))
                            xseccsv.writerow(["P{:02d}S".format(point_number), ipll[1], ipll[0], current_point.plus(lhpoint([1, 0])).vector()[0], current_point.plus(lhpoint([1, 0])).vector()[1]])

                    # if flowing SE, evaluate 1 point left (East)
                    elif flow_direction == 7 and dem_v[current_point.plus(lhpoint([0, 1])).vector()] > self.psea_level:
                        seq += "+E"
                        plan_area, innund = EvalPoint(current_point.plus(lhpoint([0, 1])), plan_area)
                        if plotcsv:
                            ipll = rc2ll(dem_f, dem_crs, (current_point.plus(lhpoint([0, 1])).vector()))
                            xseccsv.writerow(["P{:02d}E".format(point_number), ipll[1], ipll[0], current_point.plus(lhpoint([0, 1])).vector()[0], current_point.plus(lhpoint([0, 1])).vector()[1]])

                    # if flowing NE, evaluate 1 point up (North)
                    elif flow_direction == 1 and dem_v[current_point.plus(lhpoint([-1, 0])).vector()] > self.psea_level:
                        plan_area, innund = EvalPoint(current_point.plus(lhpoint([-1, 0])), plan_area)
                        seq += "+N"
                        if plotcsv:
                            ipll = rc2ll(dem_f, dem_crs,(current_point.plus(lhpoint([-1, 0])).vector()))
                            xseccsv.writerow(["P{:02d}N".format(point_number), ipll[1], ipll[0], current_point.plus(lhpoint([-1, 0])).vector()[0], current_point.plus(lhpoint([-1, 0])).vector()[1]])

                    # next point
                    if flow_direction == 1:
                        current_point = current_point.plus(lhpoint([-1, 1]))
                    elif flow_direction == 2:
                        current_point = current_point.plus(lhpoint([-1, 0]))
                    elif flow_direction == 3:
                        current_point = current_point.plus(lhpoint([-1, -1]))
                    elif flow_direction == 4:
                        current_point = current_point.plus(lhpoint([0, -1]))
                    elif flow_direction == 5:
                        current_point = current_point.plus(lhpoint([1, -1]))
                    elif flow_direction == 6:
                        current_point = current_point.plus(lhpoint([1, 0]))
                    elif flow_direction == 7:
                        current_point = current_point.plus(lhpoint([1, 1]))
                    elif flow_direction == 8:
                        current_point = current_point.plus(lhpoint([0, 1]))
                    else:
                        log_msg("Error: flow direction at point {} has value {} #2. Expecting values between 1-8. "
                            "Possibly this is because the point is at the very edge of the DEM. Terminating".format(current_point.vector(), flow_direction), screen_op = False)
                        sys.exit()
                    flow_direction = flowdir_v[current_point.vector()]  # 1 = NE, 2 = N, 3 = NW...continuing ACW until 8 = E. Some minus error values can exist on the edges
                    point_number += 1
                if flow_direction <= 0:
                    log_msg("Warning: flow direction at point {} has value {} #2. Expecting values between 1-8. "
                        "This is because the lahar has reached the very edge of the DEM.".format(current_point.vector(), flow_direction), screen_op = False)

                return innund

            ##############################################################################################
            log_msg("Generating flows...", frame = self)

            log_msg("Preparing flow directory", frame = self)
            plahar_dir = os.sep.join([os.getcwd(),self.pwdir, self.plahar_dir])

            # If folder doesn't exist, then create it.
            if not os.path.isdir(plahar_dir):
                os.makedirs(plahar_dir)
            else:
                files = [f for f in os.listdir(plahar_dir) if os.path.isfile(os.path.join(plahar_dir, f))]
                for fname in files:
                    try:
                        log_msg("Removing file {} from flow directory {}".format(fname, self.plahar_dir), screen_op = False)
                        os.remove(os.sep.join([plahar_dir, fname]))
                    except: #maybe to use OSError as eception type
                        log_msg("Error: whilst deleting previous files from directory {} file {} unavailable - possibly locked in another application (eg QGIS)".format(self.plahar_dir, fname), errmsg = True, frame = self)
                        return True
                os.rmdir(plahar_dir)
                os.makedirs(plahar_dir)

            if sys_parms['pplotxsecarea'][0]:
                log_msg("Preparing cross sectional area graphics directory", frame = self)
                pcrosssec_area_dir = os.sep.join([os.getcwd(),self.pwdir, sys_parms['pxsecareadir'][0]])

                # If folder doesn't exist, then create it.
                if not os.path.isdir(pcrosssec_area_dir):
                    os.makedirs(pcrosssec_area_dir)
                else:
                    files = [f for f in os.listdir(pcrosssec_area_dir) if os.path.isfile(os.path.join(pcrosssec_area_dir, f))]
                    for fname in files:
                        try:
                            log_msg("Removing file {} from cross sectional area graphics directory {}".format(fname, pcrosssec_area_dir), screen_op = False)
                            os.remove(os.sep.join([pcrosssec_area_dir, fname]))
                        except: #maybe to use OSError as eception type
                            log_msg("Error: whilst deleting previous files from directory {} file {} unavailable - possibly locked in another application".format(pcrosssec_area_dir, fname), errmsg = True, frame = self)
                            return True
                    os.rmdir(pcrosssec_area_dir)
                    os.makedirs(pcrosssec_area_dir)

            log_msg("Loading DEM...", frame = self)
            pdem_fn = os.sep.join([os.getcwd(),self.pwdir, self.pdem_fn])

            dem_f, dem_crs, dem_v = LoadFile(pdem_fn)

            # todo 1) find a method of determing the cell size from the input file. Using the transform method is different depending on the
            # projection method. It will return meters or degrees. Currently the cell distance is just calculated from the distance between
            # two cells. This results in a slightly different value than using the transform method
            # todo 2) currently assumes cells in the matrix are square. This may not be appropriate for some project methods/tif files

            # dem_cell_size = dem_f.transform[0]
            dem_cell_size = rcdist(dem_f, dem_crs, (0, 0), (0, 1))  # distance in x direction, ie one column

            nrows = dem_v.shape[0]
            ncols = dem_v.shape[1]

            # Load Flow Direction file
            log_msg("Loading Flow Direction file...", frame = self)
            pflow_fn = os.sep.join([os.sep.join([os.getcwd(), self.pwdir]), self.pflow_fn])
            flowdir_f, flowdir_crs, flowdir_v = LoadFile(pflow_fn)
            if flowdir_v.shape != dem_v.shape or dem_crs != flowdir_crs:
                log_msg("Error: mismatch in raster size and projection between DEM file ({}) and Flow Direction file ({})".format(self.pdem_fn, self.pflow_fn), errmsg = True, frame = self)
                return True

            log_msg("Loading Initiation Points...", frame = self)
      
            # read from csv
            if sys_parms['ripcsv'][0] != "":
                log_msg("Points loaded from csv file: " + sys_parms['ripcsv'][0] + " in " + os.sep.join([os.getcwd(), self.pwdir]), screen_op = False)
                try:
                    ipload = open(os.sep.join([os.getcwd(), self.pwdir, sys_parms['ripcsv'][0]]), newline='')
                    ipreader = csv.reader(ipload)
                    ipdata = list(ipreader)
                except:
                    log_msg("Error: attempting to load initation points from {} in {} but file unavailable. Possibly locked in another application (eg Excel) ". \
                            format(sys_parms['ripcsv'][0], os.sep.join([os.getcwd(), self.pwdir])), errmsg = True, frame = self)
                    return True

                # if ipload.ndim == 1: # a single line is enumerated by element rather than by line
                #     ipload = np.reshape(ipload, (1, ipload.size))
                ips = []
                for i, line in enumerate(ipdata):
                    if not i == 0 and line[0] != 'Apex':
                        if sys_parms['userowcol'][0]:
                            r_in = int(line[4])
                            c_in = int(line[5])
                        else:
                            # file is sequenced latitude and longitude for presentation consistency. The programme uses
                            # longitude and latitude to align to x,y axis. Hence the order read in needs to be reversed.
                            r_in, c_in = ll2rc(dem_f, dem_crs, [float(line[1]), float(line[2])])
                        if 0 <= r_in < nrows and 0 <= c_in < ncols:
                            ips.append([line[0], r_in, c_in, line[2], line[1]])
                        else:
                            log_msg("Warning: Point {} ignored as it is outside the DEM file".format(line[0]), screen_op = False)

            else:
                #read from gpkg
                pinitpoints_fn = os.sep.join([os.getcwd(), self.pwdir, self.pinitpoints_fn])
                log_msg("Points loaded from gpkg file: " + pinitpoints_fn, screen_op = False)
                d = gpd.GeoDataFrame.from_file(pinitpoints_fn)
                ips = []
                for i, g in zip(d['index'], d['geometry']): 
                    if g is not None: #traps deleted points
                        if g.geom_type == 'Point' and i != 'Apex' and not g.is_empty:
                            r_in, c_in = ll2rc(dem_f, dem_crs, [g.x, g.y])
                            if 0 <= r_in < nrows and 0 <= c_in < ncols:
                                ips.append([i, r_in, c_in, g.x, g.y])
                            else:
                                log_msg("Warning: Point {} ignored as it is outside the DEM file".format(i), screen_op = False)

            if len(ips)> 0:

                # Calculate Lahars
                log_msg("Generating Flows...", frame = self)
                innund_total_v = np.zeros_like(dem_v).astype(int)  # array for total innundations
                for v1, v in enumerate(self.pvolume_value):
                    innund_vol_v = np.zeros_like(dem_v).astype(np.uint)  # array for all innundations for a particular volume

                    for i, ip in enumerate(ips):
                        log_msg("Generating Flow. Initiation Point: {}/{}   Volume: {:.2e} {}/{} ".format(i + 1, len(ips), v, v1 + 1, len(self.pvolume_value)), frame = self)
                        innund_v = gen_lahar(v, ip)

                        ofn = "{}-V{:.2e}".format(ip[0], v).replace("+", "").replace(".", "-")
                        log_msg("Created flow at {} Latitude: {} Longitude: {} Row: {} Column: {} Volume: {} Filename: {}".format(ip[0], ip[4], ip[3], ip[1], ip[2], v, ofn), screen_op=False)  # todo file extension?

                        ofn = os.sep.join([os.getcwd(), self.pwdir, self.plahar_dir, ofn])
                        log_msg("Writing : {}".format(ofn), screen_op=False)
                        SaveFile(ofn, dem_f, dem_crs, innund_v)
                        innund_vol_v = np.where(innund_vol_v == 0, innund_v * (i+1), innund_vol_v)  # add innundation for one initiation point and volume to the overall volume array

                    # save overall volume file
                    ofn = "V{:.2e}".format(v).replace("+", "").replace(".", "-")
                    ofn = os.sep.join([os.getcwd(), self.pwdir, self.plahar_dir, ofn])
                    log_msg("Writing : {}".format(ofn, ), screen_op=False)
                    SaveFile(ofn, dem_f, dem_crs, innund_vol_v)
                    innund_total_v = np.where(innund_total_v == 0, (innund_vol_v > 0) * (v1 + 1), innund_total_v)  # add volume innundation to the total innundation

                # save total innundation array
                ofn = "Total"
                ofn = os.sep.join([os.getcwd(), self.pwdir, self.plahar_dir, ofn])
                log_msg("Writing : {}".format(ofn, ), screen_op=False)
                SaveFile(ofn, dem_f, dem_crs, innund_total_v)
                log_msg("Finished", frame = self)
                return False
            else:
                log_msg("Error - no valid initiations points", errmsg = True, frame = self)
                return True

        load_parameters()
        self.frame = create_frame()
        title(10)
        DEM_file(20)
        if self.pthal_fn !="":
            thal_file(30)
        flow_file(40)
        initpoints_file(50)
        volume(55)
        scenario(60)
        c1_value(70)
        c2_value(80)
        display_formula(100)
        sea_level(110)
        lahar_dir(120)
        back_button(130)
        lahar_button(130)
        status_msg(140)

def lltransform(ll, dist, bearing):
    """returns new lon, lat of point [dist] away from [ll] at bearing [bearing]"""

    #todo - should this not use the geod of the DEM tif file?
    end_lon, end_lat, backaz = geod.fwd(ll[0], ll[1], bearing, dist)
    return (end_lon, end_lat)

def log_msg(msg, screen_op = True, file_op = True, errmsg = False, initfile = False, timestamp = 'True', **kwargs):
    """logs message"""
    dt = datetime.datetime.now()
    if screen_op:
        if 'frame' in kwargs:
            frame = kwargs['frame']
            frame.tk_statusmsg["text"] = msg
            if not errmsg:
                frame.tk_statusmsg["fg"] = "black"
            else:
                frame.tk_statusmsg["fg"] = "red"
            frame.update()

    if timestamp:
        msg = "{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d} ".format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) + msg
    if file_op:
        if initfile:
            f_log = open(log_fn, 'w')
        else:
            f_log = open(log_fn, 'a')
        f_log.write(msg +'\n')
        f_log.close

def validate_file_to_write(fn_in, dir, frame, ovr_msg, **kwargs):

    # kwargs
    # extend: if no file type specified, use this one
    # type: test against this file type
    # exists: True to test if file already exists; asks for confirmation of the overwrite

    def press_overwrite():
        nonlocal error, error_msg, cancel_flag, fnp
        try:
            # f = open(fnp, "a")
            # f.close()
            error = False
            error_msg = ""
            cancel_flag = False

        except: #maybe to use OSError as eception type
            error = True
            error_msg = "Error: File unavailable - possibly locked in another application (eg QGIS)"
            cancel_flag = False
            
        proceed.set(True)

    def press_cancel():
        nonlocal error, error_msg, cancel_flag
        error = False
        cancel_flag = True
        error_msg = ""
        proceed.set(True)

    #test if follows the format ######.###
    
    fn = fn_in.strip().split(".") #removes leading and trailing spaces
    if not 0 < len(fn) <= 2:
        return fn_in, True, False, "Error: Invalid file name"
    
    if fn[0] == "":
        return "", True, False, "Error: File not specified"
        
    # add extension
    if len(fn) ==1:
        if not 'extend' in kwargs:
            return fn_in, True, "Error: Invalid file name - no extension specified"
        else:
            fn.append(kwargs['extend'])        
        
    #test valid characters
    if not(all([x in sys_parms['ok_chars'][0] for x in fn[0]]) and all([x in sys_parms['ok_chars'][0] for x in fn[1]])):
        return fn_in, True, False, "Error: Invalid characters in filename"
    
    # test extension
    if 'type' in kwargs:
        if fn[1] != kwargs['type']:
            return fn_in, True, False, "Error: Invalid type. Type " + kwargs['type'] + " only"

    fn = fn[0] + "." + fn[1]
    # test if already exists
    if 'exists' in kwargs:
        if kwargs['exists']:
            error = False
            cancel_flag = False
            error_msg = ""
            fnp = os.sep.join([os.getcwd(), dir, fn])
            if os.path.isfile(fnp):
                # freeze frame
                freeze_list = []
                for child in frame.winfo_children():
                        freeze_list.append([child, child.cget('state')])
                        child.configure(state='disabled')

                # create pop out from frame
                po_toplvl = tk.Toplevel()
                po_toplvl.protocol("WM_DELETE_WINDOW", press_cancel)
                po_toplvl.columnconfigure(0, weight = 1)
                po_toplvl.rowconfigure(0, weight = 1)
                po_toplvl['borderwidth'] = 50

                frame1 = tk.Frame(po_toplvl)
                frame1.columnconfigure(0, weight = 1)
                frame1.rowconfigure(0, weight = 1)
                frame1.grid(row = 0, column = 0, padx = 10, sticky=tk.NSEW)

                frame2 = tk.Frame(po_toplvl)
                frame2.columnconfigure(0, weight = 1)
                frame2.rowconfigure(0, weight = 1)
                # frame2.grid(row = 1, column = 0, padx = 10, sticky=tk.EW)
                frame2.grid(row = 1, column = 0)

                tk.Label(frame1, text=ovr_msg, font=('Helvetica', 12, 'bold')).grid(row=10, column = 0, padx = 10, columnspan=2, sticky='W')
                tk.Label(frame1, text='File ' + fn +' already exists in ' + dir, font=('Helvetica', 12)).grid(row=20, column = 0, padx = 10, columnspan=2, sticky='W')
                tk.Label(frame1, text = '').grid(row=30, column = 0, padx = 10, columnspan=1, sticky='W')

                tk_overwrite_button = tk.Button(frame2, text="Overwrite", font=('Helvetica', 12), command=press_overwrite)
                tk_overwrite_button.grid(row=0, column = 0, padx = 10, columnspan=1, sticky = 'E')
                tk_cancel_button = tk.Button(frame2, text="Cancel", font=('Helvetica', 12), command = press_cancel)
                tk_cancel_button.grid(row=0, column = 1, padx = 10, columnspan=1, sticky = 'W')

                #pause execution until button is pressed
                proceed = tk.BooleanVar()
                proceed.set(False)
                tk_cancel_button.wait_variable(proceed)

                #unfreeze frame
                for i in freeze_list:
                        i[0].configure(state=i[1])
                #remove pop up
                po_toplvl.destroy()
                if cancel_flag:
                    return fn_in, error, cancel_flag, error_msg
                else:
                    return fn, error, cancel_flag, error_msg

    return fn, False, False, ""

def validate_dir_to_write(dir_in, wdir, frame, ovr_msg, **kwargs):

    # kwargs
    # exists: True to test if dir already exists

    def press_overwrite():
        nonlocal error, error_msg, cancel_flag, dir

        error = False
        error_msg = ""
        cancel_flag = False

        files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
        for fname in files:
            fname_path = os.sep.join([dir_path, fname])
            try:
                # f1 = open(fname_path, "a")
                # f1.close()
                pass
            except: #maybe to use OSError as eception type
                error = True
                error_msg = "Error: Files in directory {} unavailable - possibly locked in another application (eg QGIS)".format(dir)

        proceed.set(True)

    def press_cancel():
        nonlocal error, error_msg, cancel_flag
        error = False
        cancel_flag = True
        error_msg = ""
        proceed.set(True)

    #test valid characters
    dir = dir_in.strip()
    if dir == "":
        return dir, True, False, "Error: Directory not specified"
    
    if not(all([x in sys_parms['ok_chars'][0] for x in dir])):
        return dir, True, False, "Error: Invalid characters in directory name"
    
    # test if already exists
    if 'exists' in kwargs:
        if kwargs['exists']:
            error = False
            cancel_flag = False
            error_msg = ""
            
            dir_path = os.sep.join([os.getcwd(), wdir, dir])
            if os.path.isdir(dir_path):
                # freeze frame
                freeze_list = []
                for child in frame.winfo_children():
                        freeze_list.append([child, child.cget('state')])
                        child.configure(state='disabled')

                # create pop out from frame
                po_toplvl = tk.Toplevel()
                po_toplvl.protocol("WM_DELETE_WINDOW", press_cancel)
                po_toplvl.columnconfigure(0, weight = 1)
                po_toplvl.rowconfigure(0, weight = 1)
                po_toplvl['borderwidth'] = 50

                frame1 = tk.Frame(po_toplvl)
                frame1.columnconfigure(0, weight = 1)
                frame1.rowconfigure(0, weight = 1)
                frame1.grid(row = 0, column = 0, padx = 10, sticky=tk.NSEW)

                frame2 = tk.Frame(po_toplvl)
                frame2.columnconfigure(0, weight = 1)
                frame2.rowconfigure(0, weight = 1)
                # frame2.grid(row = 1, column = 0, padx = 10, sticky=tk.EW)
                frame2.grid(row = 1, column = 0)

                tk.Label(frame1, text=ovr_msg, font=('Helvetica', 12, 'bold')).grid(row=0, column = 0, padx = 10, columnspan=2, sticky='W')
                tk.Label(frame1, text='Directory ' + dir +' already exists in ' + wdir, font=('Helvetica', 12)).grid(row=1, column = 0, padx = 10, columnspan=2, sticky='W')
                tk.Label(frame1, text = '').grid(row=2, column = 0, padx = 10, columnspan=1, sticky='W')

                tk_overwrite_button = tk.Button(frame2, text="Overwrite", font=('Helvetica', 12), command=press_overwrite)
                tk_overwrite_button.grid(row=0, column = 0, padx = 10, columnspan=1, sticky = 'E')
                tk_cancel_button = tk.Button(frame2, text="Cancel", font=('Helvetica', 12), command = press_cancel)
                tk_cancel_button.grid(row=0, column = 1, padx = 10, columnspan=1, sticky = 'W')

                #pause execution until button is pressed
                proceed = tk.BooleanVar()
                proceed.set(False)
                tk_cancel_button.wait_variable(proceed)

                #unfreeze frame
                for i in freeze_list:
                        i[0].configure(state=i[1])
                #remove pop up
                po_toplvl.destroy()

                if cancel_flag:
                    return dir_in, error, cancel_flag, error_msg
                else:
                    return dir, error, cancel_flag, error_msg

    return dir, False, False, ""

def validate_file_to_read(fn_in, dir, **kwargs):
    fn = fn_in.strip()
    fnp = os.sep.join([os.getcwd(), dir, fn])
    if not os.path.isfile(fnp):
        return fn, True, "Error: File does not exist in directory " + dir
    
    if 'type' in kwargs:
        exten = fn.split(".")[1]
        if kwargs['type'] != exten:
            return fn, True, "Error: Only files with extension " + kwargs['type']

    return fn, False, ""

def validate_dir_to_read(dir_in):
    dir = dir_in.strip()
    if dir == "":
        return dir, True, "Error: Enter a valid sub directory in  " + os.getcwd()
    dirp = os.sep.join([os.getcwd(), dir])
    if not os.path.isdir(dirp):
        return dir, True, "Error: Directory does not exist in  " + os.getcwd()
    
    return dir, False, ""

def validate_numeric(value, **kwargs):
    if 'zero' in kwargs:
        if kwargs['zero']:
            if value == '':
                value = 0
    try:
        value = float(value)
    except:
        return value, True, "Error: Values must be numeric"

    if 'gt' in kwargs:
        if not value > kwargs['gt']:
            return value, True, "Error: Values must be greater than " + str(kwargs['gt'])

    if 'range' in kwargs:
        if not kwargs['range'][0] <= value <= kwargs['range'][1]:
            return value, True, "Error: Values must be between " + str(kwargs['range'][0]) + ' and ' + str(kwargs['range'][1])

    return value, False, ""

def LoadFile(fn):
    """ Loads a .tif or text file (.asc or .txt)"""
    try:
        f = rio.open(fn)
    except:
        log_msg("File not found: " + fn)
        sys.exit() #shouldnt happen

    if fn[-3:] == "txt" or fn[-3] == "asc":  # ascii file
        fcrs = pj.Proj("EPSG:4326")
    elif fn[-3:] == "tif":  # tif file
        fcrs = pj.Proj(f.crs)
    else:
        log_msg("Unrecognised file type for file name:{}. Terminating".format(fn))
        sys.exit() #shouldnt happen

    v = f.read(1)

    return f, fcrs, v

def SaveFile(fn, ref_f, ref_crs, v):
    """ Saves a matrix as a .tif file, an Ascii file (.txt) or a .csv file"""
    # Although possible to save an as Ascii file there seems no particular reason to do so. Savingg as a csv file is convenient
    # for debugging. Recommend that the file is saved as a .tif file

    fn = fn.split(".")[0]
    # entry screen provides file names with extensions. These are ignored in program and the paramters pwritexxx are used instead to control output.
    
    if sys_parms['pwritetif'][0]:
        resolve_inout(overwrite=True)
        profile = ref_f.profile
        # profile.update(dtype=rio.uint8, count=1, compress='lzw', nodata = 255)
        profile.update(dtype=rio.uint16, nodata = 0)
        with rio.Env():
            with rio.open(fn + ".tif", 'w', **profile) as dst:
                dst.write(v.astype(rio.uint16), 1)
    if sys_parms['pwriteascii'][0]:
        f = open(fn + ".txt", "w")
        f.write("ncols " + str(v.shape[1]) + "\n")
        f.write("nrows " + str(v.shape[0]) + "\n")
        row = col = 0
        east, north = ref_f.xy(row, col, offset='ll')  # spatial --> image coordinates
        lon, lat = ref_crs(east, north, inverse=True)
        f.write("xllcorner " + str(lon) + "\n")
        f.write("yllcorner " + str(lat) + "\n")
        f.write("cellsize " + str(ref_f.transform[0]) + "\n")
        f.write("NODATA_value 255")
        for i in reversed(v):
            f.write(" ".join(map(str, map(int, i))) + "\n")
        f.close()

    if sys_parms['pwritecsv'][0]:
        np.savetxt(fn + ".csv", v, delimiter=",")

def rc2ll(f, crs, rc):
    """converts row and column to lon and lat"""
    # places at centre of cell - not se corner
    east, north = f.xy(rc[0], rc[1])  # spatial --> image coordinates
    lon, lat = crs(east, north, inverse=True)
    return (lon, lat)

def rcdist(f, crs, rc1, rc2):
    """returns the distance between two points based on row and column"""
    ll1 = rc2ll(f, crs, rc1)
    ll2 = rc2ll(f, crs, rc2)
    forward_az, backward_az, distance = geod.inv(ll1[0], ll1[1], ll2[0], ll2[1])
    return distance

def ll2rc(f, crs, ll):
    """converts lon and lat to row and column"""
    east, north = crs(ll[0], ll[1])
    row, col = f.index(east, north)  # spatial --> image coordinates
    return (row, col)

def load_sys_parms():
    try:
        sys_parms = pickle.load(open(os.sep.join([os.getcwd(), "sys_parameters.pickle"]), "rb"))
        # sys_parms['dy'] = [float(1), "Height increment", "Height increment used to calculate flows"]
        # pickle.dump(sys_parms, open(os.sep.join([os.getcwd(), "sys_parameters.pickle"]), "wb"))

    except:
        #Initiation Points
        sys_parms = {}
        # ['variable value', 'label', 'description']
        sys_parms['log_file_name'] = ['log', 'Log file', "Name of the log file"]
        sys_parms['single_log_file'] = [False, 'Use single log file', 'Check to use a single log file. Unchecked will create a log file for each run, suffixed by date-time']
        sys_parms['ok_chars'] = ["-_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", \
                                 "Allowable characters", "List of allowable characters for file names"]
        sys_parms['wipcsv'] = ["", "Write Initiation Points to csv", "Enter a csv file name to write initiation points to csv as well as the gpkg file"]
        sys_parms['ripcsv'] = ["", "Read Inititiation Points from csv", "Enter a csv file name to read initiation points this file instead of the gpkg file"]
        sys_parms['userowcol'] = [False, "Use Row/Column", "Uses the row/colum if the intitation points are loaded from csv file; otherwise uses lat/lon"]
        sys_parms['ecraw_fn'] = ["", "Energy Cone - Raw file", "Enter a tif filename to write the raw energy cone to"]
        sys_parms['ecfilled_fn'] = ["", "Energy Cone - Filled file", "Enter a tif filename to write the filled energy cone to"]
        sys_parms['ec_fn'] = ["", "Write Energy Cone Line points to csv", "Enter a csv file name to write the energy cone line points to csv"]
        # sys_parms['ptextcrs'] = ["EPSG:4326", "Ascii file CRS", "CRS to use if reading data from ASCII files"]
        sys_parms['povr_hl_ratio'] = [True, "Override H/L Ratio limits", "Check to override limit on HL Ratios of values between 0.2 and 0.3"]
        sys_parms['pwritetif'] = [True, "Output as tif", "Write all output as tif files"]
        sys_parms['pwriteascii'] = [False, "Output as ascii", "Write all output as ascii files (additionally)"]
        sys_parms['pwritecsv'] = [False, "Output as csv", "Write all output as csv files (additionally)"]
        #Lahars
        sys_parms['pscenario_values'] = [['Lahar', 'Debris', 'Pyroclastic', 'Custom'], "Flow scenarios", "List of types of flow. Include Custom as the last entry to enable customised parameters"]
        sys_parms['pc1_values'] = [[0.05,0.1, 0.05], "Co-efficent #1", "Proportionality coefficient for the cross sectional area"]  
        sys_parms['pc2_values'] = [[200, 20, 35], "Co-efficent #2", "Proportionality coefficient for the planar area"]
        sys_parms['dy'] = [float(1), "Height increment", "Height increment used to calculate flows"]
        sys_parms['pplotxsecarea'] = [False, "Plot cross sectional area graphics", "Select to plot graphics of the cross sectional area"]
        sys_parms['pxsecareadir'] = ["CrossSections", "Cross Sectional Area Directory", "Directory in which cross sectional area graphics will be placed"]
        sys_parms['pplotip'] = ["", "Initiation Point", "Initiation point for cross sectional area eg IP01"]
        sys_parms['pplotvol'] = ["", "Volume", "Volume for cross sectional area eg 1e5"]
        sys_parms['pxsec_fn'] = ["", "Lahar Points", "Enter a csv filename to write the points on the lahar for the ip and volume specified above"]

        pickle.dump(sys_parms, open(os.sep.join([os.getcwd(), "sys_parameters.pickle"]), "wb"))

    return sys_parms
        

########################################################################################################################################
# if __name__ == '__main__':
# Execute programme on import
# Load system parameters
sys_parms = load_sys_parms()

# intitialise log file
if sys_parms['single_log_file'][0]:
    log_fn = sys_parms['log_file_name'][0]
else:
    dt = datetime.datetime.now()
    log_fn = sys_parms['log_file_name'][0].split(".")[0] \
        + " {:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}".format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) + '.txt'
log_fn = os.sep.join([os.getcwd(), log_fn])

log_msg("LaharZ Starting\n", initfile = True, screen_op=False)
log_msg("System Parameters", screen_op = False)
for pk in sys_parms.keys():
    log_msg("Parameter: " + pk + "Value: " + str(sys_parms[pk][0]))

geod = pj.Geod(ellps='WGS84')  # used as the projection method to determine distances between two points

app1 = LaharZ_app()
app1.mainloop()
