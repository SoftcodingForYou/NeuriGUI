import tkinter                              as tk
from sys                                    import platform
import serial.tools.list_ports
import customtkinter
import os

class Parameters:

    def __init__(self):

        super(Parameters, self).__init__()

        self.set_defaults()
        self.get_screen_info()
        self.build_frontend()

        # This stops code execution until paramWin closed
        self.paramWin.mainloop()


    def set_defaults(self):

        self.all_set        = False
        
        #GUI settings
        self.img_helment    = './frontend/Isotipo-Helment-color.png'
        if os.path.exists('./frontend/darkmode.txt'):
            with open('./frontend/darkmode.txt') as f:
                themeline   = f.read()
                if themeline == 'Darkmode=1':
                    self.darkmode = True
                else:
                    self.darkmode = False
        else:
            self.darkmode = False

        #Session-specific parameters
        self.yrange         = [-0, 0] # List of scalars ([negative, positive]) in order to set figure y axis range
        self.notch          = 0 # Integer 0 (Off), 50 (50 Hz) or 60 (60 Hz)
        self.bpass          = 0 # Integer -1 to 3 according to number of options in "frequency_bands" below
        self.dispenv        = False # Boolean 0 (Off), 1 (On)
        self.set_customsession = False

        #Signal arrays
        self.sample_rate    = 200 #Hertz
        self.max_chans      = 8 #scalar (Max. amount of input channels of board)
        self.selected_chans = [True] * self.max_chans
        self.buffer_length  = 10 #scalar (seconds)
        self.buffer_add     = 4 #scalar (seconds), we add this to the buffer for filtering to avoid edge artifacts
        self.sample_count   = 0 #integer zero
        self.saving_interval= 1 #scalar (seconds)
        self.PGA            = 24 #scalar

        #Signal reception
        self.baud_rate      = 115200 #scalar default baudrate for connection
        self.port           = '' #Leave blank
        self.protocols      = {}
        self.protocols["USB"]= 2
        self.protocols["BT"]= 3
        self.firmfeedback   = self.protocols["USB"]
        self.time_out       = None #Wait for message

        # Signal relay
        self.udp_ip         = "127.0.0.1" # Loopback ip for on-device communication

        #Plotting
        # self.plot_intv       = 200 #scalar defining update rate of figure (ms) OBSOLETE PARAMETER
        self.s_down         = 5 #Desired downsampling factor (buffer_length*sample_rate/s_down must be convertable to integer)


        #Signal processing
        self.filter_order   = 3 #scalar
        self.frequency_bands= {
            'LineNoise':    (46, 54),
            'LineNoise60':  (56, 64),
            'Sleep':        (1, 30),
            'Theta':        (4, 8),
            'Whole':        (0.5, 45)}


    def build_frontend(self):

        self.framePadX          = 20
        self.framePadY          = 10
        self.widgetPadX         = 10
        self.widgetPadY         = 5
        
        # Build GUI
        # -----------------------------------------------------------------
        self.paramWin           = customtkinter.CTk()
        pixels_x, pixels_y      = int(
            round(0.8*self.screen_width)), int(round(0.9*self.screen_height))
        x_cordinate, y_cordinate= int((self.screen_width/2) - (pixels_x/2)), int(0)
        self.paramWin.geometry("{}x{}+{}+{}".format(
            pixels_x, pixels_y, x_cordinate, y_cordinate))

        if self.darkmode:
            customtkinter.set_appearance_mode("dark")
        else:
            customtkinter.set_appearance_mode("light")
        customtkinter.set_default_color_theme("blue")

        self.paramWin.title('Settings (close when ready)')

        # Add options
        self.display_ports(self.add_frame_ext_x())
        self.display_protocol(self.add_frame_ext_x())
        self.display_gains(self.add_frame_ext_x())
        self.display_samplingrate(self.add_frame_ext_x())
        self.display_timerange(self.add_frame_ext_x())
        self.display_channels(self.add_frame_ext_x())
        self.display_output_name(self.add_frame_ext_x())
        self.display_speed_up(self.add_frame_ext_x())
        
        # Set GUI interaction behavior
        self.paramWin.lift()
        self.paramWin.attributes("-topmost", True)
        self.paramWin.after_idle(self.paramWin.attributes, '-topmost', False)

        # Set closing sequence
        # -----------------------------------------------------------------
        # Just closing the window makes the sampling process hang. We 
        # prevent this by setting up a protocol.
        self.paramWin.protocol('WM_DELETE_WINDOW', self.on_closing)


    def add_frame_ext_x(self):
        frameMain               = customtkinter.CTkFrame(master=self.paramWin)
        frameMain.pack(pady=self.framePadY, padx=self.framePadX, fill="both", expand=True)
        return frameMain
        
    
    def get_screen_info(self):

        root = tk.Tk()
        # Get information about screen to center the windows
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()


    def display_ports(self, master):

        ports = [port.device for port in list(serial.tools.list_ports.comports())]
        if len(ports) == 0:
            defaultPort = 'No port available'
        else: 
            defaultPort = ports[0]
            self.port   = defaultPort # If no change, select_port does not get triggered

        labelPort = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Select port')
        labelPort.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)
        portMenu = customtkinter.CTkOptionMenu(master, values=ports,
                                               command=self.select_port)
        portMenu.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT, expand=True)
        portMenu.set(defaultPort)

        infoText = """
            You seem to use a GNU/Linux-based OS. Make sure you are part of
            the "dialout" and "uucp" groups by running:
                > sudo usermod -a -G dialout $USER
                > sudo usermod -a -G uucp $USER
            in the terminal in order to use the system's ports without root.
        """

        if platform == "linux" or platform == "linux2":
            labelLinux = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text=infoText)
            labelLinux.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.RIGHT)


    def select_port(self, event):

        self.port       = event
        print('Port set to {}'.format(self.port))


    def display_protocol(self, master):

        labelProt = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Select connection protocol')
        labelProt.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)

        self.prot_var  = tk.DoubleVar(value=self.firmfeedback)

        protocolKeys = list(self.protocols.keys())
        protocolVals = list(self.protocols.values())

        for i in range(len(self.protocols)):
            rb = customtkinter.CTkRadioButton(master=master,
                                              variable=self.prot_var,
                                              value=protocolVals[i],
                                              text=str(protocolKeys[i]),
                                              command=self.select_protocol)
            rb.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT, expand=True)


    def select_protocol(self):
        
        self.firmfeedback = self.prot_var.get()
        print('Will send a \"{}\" to board'.format(self.firmfeedback))


    def display_gains(self, master):

        gains = ['2', '4', '8', '24']
        idx_def = [i for i in range(len(gains)) if int(gains[i]) == self.PGA]

        labelGain = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Select gain')
        labelGain.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)
        gainMenu = customtkinter.CTkOptionMenu(master, values=gains,
                                                    command=self.select_gain)
        gainMenu.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT, expand=True)
        gainMenu.set(gains[int(idx_def[0])])


    def select_gain(self, event):

        self.PGA = int(event)
        print('PGA set to {}'.format(self.PGA))


    def display_samplingrate(self, master):
        
        self.labelSfr = customtkinter.CTkLabel(master=master, 
            justify=customtkinter.LEFT,
            text='Optional: Set sampling rate')
        self.labelSfr.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)

        self.labelInfo = customtkinter.CTkLabel(master=master, 
            justify=customtkinter.LEFT,
            text='Caution: Setting wrong values will corrupt data visualization')
        self.labelInfo.pack(pady=(0, self.widgetPadY), padx=self.widgetPadX, side=tk.BOTTOM)

        self.textSfr = customtkinter.CTkEntry(master=master,
                                           width=200, height=15,
                                           placeholder_text=str(self.sample_rate))
        self.textSfr.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT, fill=tk.X, expand=True)

        self.buttonValidate = customtkinter.CTkButton(master=master,
                                                 command=self.select_sampling_rate,
                                                 text='Validate')
        self.buttonValidate.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)


    def select_sampling_rate(self):

        try:
            newSR = int(self.textSfr.get())

            if newSR >= 100:
                self.sample_rate = newSR
                self.labelInfo.configure(text='Sampling rate set to {} Hz'.format(self.sample_rate),
                                        text_color='green')
                print('Sampling rate set to {}.'.format(self.sample_rate))
            else:
                print('Sampling rate must be at least 100 Hz. Reverting back to {} Hz'.format(self.sample_rate))
                self.labelInfo.configure(text='Sampling rate must be at least 100 Hz. Reverting back to {} Hz'.format(self.sample_rate),
                                        text_color='red')
                self.textSfr.configure(placeholder_text='Sampling rate changed to ' + str(self.sample_rate))
        except:
            print('Please enter an integer value. Reverting back to {} Hz'.format(self.sample_rate))
            self.labelInfo.configure(text='Please enter an integer value. Reverting back to {} Hz'.format(self.sample_rate),
                                     text_color='red')


    def display_timerange(self, master):

        labelRange = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Select time range to display')
        labelRange.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)
        
        ranges          = [5, 10, 20]
        idx_def         = [i for i in range(len(ranges)) if int(ranges[i]) == self.buffer_length]

        self.range_var = customtkinter.IntVar(value=ranges[int(idx_def[0])])

        for i in range(len(ranges)):
            rb = customtkinter.CTkRadioButton(master=master,
                                              variable=self.range_var,
                                              value=ranges[i],
                                              text=str(ranges[i]) + ' s',
                                              command=self.select_timerange)
            rb.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT, expand=True)


    def select_timerange(self):
        
        self.buffer_length = self.range_var.get()
        print('Time range to display set to {} s'.format(self.buffer_length))


    def display_channels(self, master):

        labelChans = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Channels to display\n(Only affects the visualization)')
        labelChans.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)

        self.channels = []
        for i in range(self.max_chans):
            self.channels.append(tk.BooleanVar())
            cb = customtkinter.CTkCheckBox(master=master,
                                            text='Ch. ' + str(i+1),
                                            command=self.select_channels,
                                            variable=self.channels[i],
                                            onvalue=True,
                                            offvalue=False)
            cb.select()
            cb.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT, expand=True)

        labelInfo = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='')
        labelInfo.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.RIGHT)


    def select_channels(self):

        for i in range(len(self.channels)):
            if self.selected_chans[i] != self.channels[i].get():
                self.selected_chans[i] = self.channels[i].get()
                if self.channels[i].get():
                    print('Channel {} enabled'.format(i))
                else:
                    print('Channel {} disabled'.format(i))


    def display_output_name(self, master):
        
        self.sessionName = 'Helment_[timestamp]'
        self.labelSession = customtkinter.CTkLabel(master=master, 
            justify=customtkinter.CENTER,
            text='Optional: Set a session name')
        self.labelSession.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)

        self.sessionInfo = customtkinter.CTkLabel(master=master, 
            justify=customtkinter.LEFT,
            text='')
        self.sessionInfo.pack(pady=(0, self.widgetPadY), padx=self.widgetPadX, side=tk.BOTTOM)

        self.textSession = customtkinter.CTkEntry(master=master,
                                           width=250, height=15,
                                           placeholder_text='Default: ' + self.sessionName)
        self.textSession.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT, fill=tk.X, expand=True)

        self.sessionValidate = customtkinter.CTkButton(master=master,
                                                 command=self.select_output_name,
                                                 text='Validate')
        self.sessionValidate.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)


    def select_output_name(self):

        newSessionName      = str(self.textSession.get())

        if len(newSessionName) > 0:
            self.sessionName    = newSessionName
            self.sessionName    = self.sessionName.replace('\n', '')
            self.set_customsession = True
            self.sessionInfo.configure(text='Session name changed to ' + str(self.sessionName),
                             text_color='green')
            print('Session named \"{}\".'.format(self.sessionName))
        else:
            self.sessionInfo.configure(text='Custom name can not be empty',
                             text_color='red')
            print('Session name can not be empty')


    def display_speed_up(self, master):

        gains = ['2', '5', '10', '20', '30', '50']
        idx_def = [i for i in range(len(gains)) if int(gains[i]) == self.s_down]

        labelSpeed = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Optional: Select downsampling intensity')
        labelSpeed.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT)
        SpeedMenu = customtkinter.CTkOptionMenu(master, values=gains,
                                                    command=self.select_speed_up)
        SpeedMenu.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.LEFT, expand=True)
        SpeedMenu.set(gains[int(idx_def[0])])

        infoText = """
            Selecting high amounts of channels and long time ranges to display can have impacts on the performance.
            You might try to compensate this by setting a higher downsampling factor. This will downsample the data
            for visualization (not the recorded data itself)
            """

        labelInfo = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text=infoText)
        labelInfo.pack(pady=self.widgetPadY, padx=self.widgetPadX, side=tk.RIGHT)


    def select_speed_up(self, event):

        self.s_down = int(event)
        print('Downsampling intensity set to {}'.format(self.s_down))
        

    def on_closing(self):

        self.paramWin.destroy()