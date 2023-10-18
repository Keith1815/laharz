import tkinter as tk
import os
from tkinter import ttk as ttk
import pickle
# import time

class mlsp_app(tk.Tk):            

    def __init__(self):
        super().__init__() #copies attributes from parent class (tk)
        self.geometry('1920x1080')
        self.title('Maintain LaharZ System Parameters')
        # self.columnconfigure(0, weight = 1)
        # self.rowconfigure(0, weight = 1)

        # # set up frame (use tk not tkk)
        m_frame = tk.Frame(self, width = 1920, height = 1080)
        
        # m_frame.columnconfigure(0, weight = 1)
        # m_frame.rowconfigure(0, weight = 1)
        m_frame.grid(row = 0, column = 0, sticky=tk.NSEW)
               
        # Add a canvas in that frame.
        self.canvas = tk.Canvas(m_frame, width = 1800, height = 1080)
        # self.canvas.columnconfigure(0, weight = 1)
        # self.canvas.rowconfigure(0, weight = 1)
        self.canvas.grid(row = 0, column = 0, padx = 10, pady = 10, sticky=tk.NSEW)

        # # Create a vertical scrollbar linked to the canvas.
        # vsbar = ttk.Scrollbar(m_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        # vsbar.grid(row=0, column = 1, sticky=tk.NS)
        # self.canvas.configure(yscrollcommand=vsbar.set)
        # self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion = self.canvas.bbox("all")))

        # # Create a horizontal scrollbar linked to the canvas.
        # hsbar = tk.Scrollbar(m_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        # hsbar.grid(row=1, column = 0, sticky=tk.EW)
        # self.canvas.configure(xscrollcommand=hsbar.set)
        self.exec_frame1() #populate widgets

    def exec_frame1(self):

        def create_frame():
            # Create a frame on the canvas to contain the widgets
            frame = tk.Frame(self.canvas)
            frame.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = tk.NW)
            # self.canvas.create_window((0,0), window = frame, anchor = "nw")
            return frame

        def title():
            # title
            tk.Label(self.frame, text='Maintain LaharZ System Parameters', font=('Helvetica', 14, 'bold')).grid(row=1, column = 0, padx = 10, columnspan=2, sticky='NW')
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=2, column = 0, padx = 10, columnspan=1, sticky='NW')

        def quit_button():
            self.tk_exit_button = tk.Button(self.frame, text='Quit', font=('Helvetica', 12))
            self.tk_exit_button.grid(row=100, column = 0, padx = 10, columnspan=1, sticky='W')
            self.tk_exit_button['command'] = press_quit_button

        def save_button():
            self.tk_exit_button = tk.Button(self.frame, text='Save & Exit', font=('Helvetica', 12))
            self.tk_exit_button.grid(row=100, column = 1, padx = 10, columnspan=1, sticky='W')
            self.tk_exit_button['command'] = press_save_button

        def status_msg(statusmsg):
            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=200, column = 0, padx = 10, columnspan=1, sticky='NW')

            self.tk_statusmsg = tk.Label(self.frame, text = statusmsg, font=('Helvetica', 12), justify = 'left')
            self.tk_statusmsg.grid(row=201, column = 0, padx = 10, columnspan=4, sticky='W')
        
        def display_parameters():
            nonlocal sys_parms, v, l
            for r, p in enumerate(sys_parms):
                tk.Label(self.frame, text = sys_parms[p][1], font=('Helvetica', 12)).grid(row=r+10, column = 0, padx = 10, pady = 2, columnspan=1, sticky='NW')
                if isinstance(sys_parms[p][0], str):
                    v.append(tk.Entry(self.frame, font=('Helvetica', 12), width = 40))
                    v[-1].grid(row=r+10, column = 1, padx = 10, pady = 2, columnspan=2, sticky='NW')
                    v[-1].insert(0, sys_parms[p][0])

                if isinstance(sys_parms[p][0], bool):
                    sys_parms[p][0] = tk.BooleanVar(value = sys_parms[p][0])
                    v.append(tk.Checkbutton(self.frame, text="", font=('Helvetica', 12), variable=sys_parms[p][0]))
                    v[-1].grid(row=r+10, column = 1, padx = 10, pady = 2, columnspan=2, sticky='NW')

                if isinstance(sys_parms[p][0], list):
                    v.append(tk.Entry(self.frame, font=('Helvetica', 12), width = 40))
                    v[-1].grid(row=r+10, column = 1, padx = 10, pady = 2, columnspan=2, sticky='NW')
                    v[-1].insert(0, ", ".join(str(x) for x in sys_parms[p][0]))

                l.append(tk.Label(self.frame, text = sys_parms[p][2], font=('Helvetica', 12), justify = 'left'))
                l[-1].grid(row=r+10, column = 4, padx = 10, pady = 2, columnspan=1, sticky='NW')

            # Blank line
            tk.Label(self.frame, text = '', font=('Helvetica', 12)).grid(row=r+20, column = 0, padx = 10, columnspan=1, sticky='NW')

        def press_save_button():
            nonlocal sys_parms, l, v
            errors = False
            bi = 0
            for i, p in enumerate(sys_parms):
                l[i]['fg'] = 'red'
                if p in {'log_file_name'}:
                    sys_parms[p][0], error, cf, l[i]['text'] = \
                        validate_file_to_write(v[i].get(), self, "Log file", "", extend = 'txt', type = 'txt')
                    v[i].delete(0, "end")
                    v[i].insert(0, sys_parms[p][0])
                    errors = error or errors
         
                if p in {'single_log_file', 'userowcol', 'povr_hl_ratio', 'pwritetif', 'pwriteascii', 'pwritecsv', 'pplotxsecarea'}:
                    # sys_parms[p][0] = sys_parms[p][0].get()
                    l[i]['text'] = ""
                
                if p in {'ok_chars', 'ptextcrs', 'p_diagonal', 'pplotip'}:
                    l[i]['text'] = ""

                if p in {'pplotvol'}:
                    l[i]['text'] = ""
                    error = False
                    if v[i].get() !="":
                        try:
                            float(v[i].get())
                        except:
                            error = True
                            l[i]['text'] = "Error: not a numeric value"
                    errors = error or errors
                
                if p in {'wipcsv', 'ec_fn', 'pxsec_fn'}:
                    sys_parms[p][0], error, cf, l[i]['text'] = \
                        validate_file_to_write(v[i].get(), self, "Log file", "", extend = 'csv', type = 'csv')
                    v[i].delete(0, "end")
                    v[i].insert(0, sys_parms[p][0])
                    errors = error or errors

                if p in {'ecraw_fn', 'ecfilled_fn'}:
                    sys_parms[p][0], error, cf, l[i]['text'] = \
                        validate_file_to_write(v[i].get(), self, "Log file", "", extend = 'tif', type = 'tif')
                    v[i].delete(0, "end")
                    v[i].insert(0, sys_parms[p][0])
                    errors = error or errors

                if p in {'ripcsv'}:
                    sys_parms[p][0], error, l[i]['text'] = \
                        validate_file_to_read(v[i].get(), extend = 'csv', type = 'csv')
                    v[i].delete(0, "end")
                    v[i].insert(0, sys_parms[p][0])
                    errors = error or errors

                if p in {'pscenario_values'}:
                    l[i]['text']  = ""
                    try: 
                        sys_parms[p][0] = v[i].get().replace(" ", "").split(",")
                    except:
                        error = True 
                        l[i]['text'] = "Error: not a recognised list"
                    errors = error or errors

                if p in {'pc1_values', 'pc2_values'}:
                    l[i]['text']  = ""
                    sys_parms[p][0] = v[i].get().split(",")

                    try: 
                        sys_parms[p][0] = v[i].get().replace(" ", "").split(",")
                    except:
                        error = True 
                        l[i]['text'] = "Error: not a recognised list"
                    if not error:
                        if "Custom" in sys_parms['pscenario_values'][0]:
                            expected_length = len(sys_parms['pscenario_values']) - 1
                        else:
                            expected_length = len(sys_parms['pscenario_values'])
                        
                        if len(sys_parms[p][0]) != expected_length:
                            error = True 
                            l[i]['text'] = "Error: not enough entries corresponding to scenarios"
                        
                    if not error:
                        for i in sys_parms[p][0]:
                            try:
                                float(i)
                            except:
                                error = True 
                                l[i]['text'] = "Error: must be numeric values"
                  
                    errors = error or errors

                if p in {'pxsecareadir'}:
                    sys_parms[p][0] = v[i].get()
                    l[i]['text'] = ""
                    if not(all([x in sys_parms['ok_chars'][0] for x in sys_parms[p][0]])):
                        error = True
                        l[i]['text'] = "Error: Invalid characters in directory name"

                    errors = error or errors

            if not errors:
                for p in sys_parms:
                    if isinstance(sys_parms[p][0], tk.BooleanVar):
                        sys_parms[p][0]= sys_parms[p][0].get()
                pickle.dump(sys_parms, open(os.sep.join([os.getcwd(), "sys_parameters.pickle"]), "wb"))
                self.destroy()
            else:
                # frame.update
                pass

        def validate_file_to_write(fn_in, dir, frame, ovr_msg, **kwargs):
            # kwargs
            # extend: if no file type specified, use this one
            # type: test against this file type
            # exists: True to test if file already exists; asks for confirmation of the overwrite

            def press_overwrite():
                nonlocal error, error_msg, cancel_flag
                try:
                    f = open(fn, "w")
                    f.close()
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
            fn = fn_in.split(".")
            if not 0 < len(fn) <= 2:
                return fn_in, True, False, "Error: Invalid file name"
            
            if fn[0] == "":
                return "", False, False, ""
                
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
                        for child in frame.winfo_children():
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
                        for child in frame.winfo_children():
                                child.configure(state='normal')
                        #remove pop up
                        po_toplvl.destroy()

                        return fn_in, error, cancel_flag, error_msg

            return fn, False, False, ""

        def validate_file_to_read(fn_in, **kwargs):
            # kwargs 
            # type - validates extension
            # extend - adds extension if not specified
            # exists - checks if file exists in cwd
            
            #test if follows the format ######.###
            fn = fn_in.split(".")
            if not 0 < len(fn) <= 2:
                return fn_in, True, "Error: Invalid file name"
            
            if fn[0] == "":
                return fn_in, False, ""
                
            # add extension
            if len(fn) ==1:
                if not 'extend' in kwargs:
                    return fn_in, True, "Error: Invalid file name - no extension specified"
                else:
                    fn.append(kwargs['extend'])        
                
            #test valid characters
            if not(all([x in sys_parms['ok_chars'][0] for x in fn[0]]) and all([x in sys_parms['ok_chars'][0] for x in fn[1]])):
                return fn_in, True, "Error: Invalid characters in filename"
            
            # test extension
            if 'type' in kwargs:
                if fn[1] != kwargs['type']:
                    return fn_in, True, "Error: Invalid type. Type " + kwargs['type'] + " only"

            fn = fn[0] + "." + fn[1]
            if 'exists' in kwargs:
                fnp = os.sep.join([os.getcwd(), fn])
                if not os.path.isfile(fnp):
                    return fn_in, True, "Error: File does not exist in directory " + os.getcwd()

            return fn, False, ""
        
        def press_quit_button():
            self.destroy()
        
        ffound = True
        try:
            sys_parms = pickle.load(open(os.sep.join([os.getcwd(), "sys_parameters.pickle"]), "rb"))
        except:
            ffound = False
            print("File {} not found in {}. To create a default system parameters file, run LaharZ. Terminating")
        
        v, l = [], [] # values, labels
        self.frame = create_frame()
        title()
        if ffound:
            display_parameters()
            statusmsg = "Welcome to Maintain LaharZ System Parameters"
            quit_button()
            save_button()

        else:
            statusmsg = "Welcome to Maintain LaharZ System Parameters. Open LaharZ to initialise system parameters"
            quit_button()

        status_msg(statusmsg)

app1 = mlsp_app()
app1.mainloop()
