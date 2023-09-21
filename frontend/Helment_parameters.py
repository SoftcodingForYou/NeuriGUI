import tkinter                              as tk
import serial.tools.list_ports
import customtkinter
import os

class Parameters:

    def __init__(self):

        super(Parameters, self).__init__()

        self.set_defaults()
        self.img_helment    = './frontend/Isotipo-Helment-color.png'

        self.get_screen_info()
        self.build_frontend()

        # This stops code execution until paramWin closed
        self.paramWin.mainloop()


    def set_defaults(self):
        
        #GUI settings
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
        self.yrange         = [-1000, 1000] # List of scalars ([negative, positive]) in order to set figure y axis range
        self.notch          = 0 # Integer 0 (Off), 50 (50 Hz) or 60 (60 Hz)
        self.bpass          = 0 # Integer -1 to 3 according to number of options in "frequency_bands" below
        self.dispenv        = False # Boolean 0 (Off), 1 (On)

        #Signal arrays
        self.sample_rate    = 200 #Hertz
        self.max_chans      = 2 #scalar (Max. amount of input channels of board)
        self.selected_chans = [True] * self.max_chans
        self.buffer_length  = 20 #scalar (seconds)
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
        
        # Build GUI
        # -----------------------------------------------------------------
        self.paramWin                = customtkinter.CTk()
        pixels_x, pixels_y      = int(
            round(0.4*self.screen_width)), int(round(0.8*self.screen_height))
        x_cordinate, y_cordinate= int((self.screen_width/2) - (pixels_x/2)), int(0)
        self.paramWin.geometry("{}x{}+{}+{}".format(
            pixels_x, pixels_y, x_cordinate, y_cordinate))

        if self.darkmode:
            customtkinter.set_appearance_mode("dark")
        else:
            customtkinter.set_appearance_mode("light")
        customtkinter.set_default_color_theme("blue")

        self.paramWin.title('Settings (close when ready)')

        frameMain               = customtkinter.CTkFrame(master=self.paramWin)
        frameMain.pack(pady=20, padx=60, fill="both", expand=True)

        # Add options
        self.display_ports(frameMain)
        self.display_protocol(frameMain)
        self.display_gains(frameMain)
        self.display_samplingrate(frameMain)
        self.display_timerange(frameMain)
        self.display_channels(frameMain)
        
        # Set GUI interaction behavior
        self.paramWin.lift()
        self.paramWin.attributes("-topmost", True)
        self.paramWin.after_idle(self.paramWin.attributes, '-topmost', False)

        # Set closing sequence
        # -----------------------------------------------------------------
        # Just closing the window makes the sampling process hang. We 
        # prevent this by setting up a protocol.
        self.paramWin.protocol('WM_DELETE_WINDOW', self.on_closing)
        
    
    def get_screen_info(self):

        root = tk.Tk()
        # Get information about screen to center the windows
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()


    def display_ports(self, master):

        ports = [port.name for port in list(serial.tools.list_ports.comports())]
        if len(ports) == 0:
            defaultPort = 'No port available'
        else: 
            defaultPort = ports[0]
            self.port   = defaultPort # If no change, select_port does not get triggered

        labelPort = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Select port')
        labelPort.pack(pady=10, padx=10)
        portMenu = customtkinter.CTkOptionMenu(master, values=ports,
                                               command=self.select_port)
        portMenu.pack(pady=0, padx=10)
        portMenu.set(defaultPort)


    def select_port(self, event):

        self.port       = event
        print('Port set to {}'.format(self.port))


    def display_protocol(self, master):

        labelProt = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Select connection protocol')
        labelProt.pack(pady=10, padx=10)

        self.prot_var  = tk.DoubleVar(value=self.firmfeedback)

        protocolKeys = list(self.protocols.keys())
        protocolVals = list(self.protocols.values())

        for i in range(len(self.protocols)):
            rb = customtkinter.CTkRadioButton(master=master,
                                              variable=self.prot_var,
                                              value=protocolVals[i],
                                              text=str(protocolKeys[i]),
                                              command=self.select_protocol)
            rb.pack(pady=0, padx=10)


    def select_protocol(self):
        
        self.firmfeedback = self.prot_var.get()
        print('Will send a \"{}\" to board'.format(self.firmfeedback))


    def display_gains(self, master):

        gains = ['2', '4', '8', '24']
        idx_def = [i for i in range(len(gains)) if int(gains[i]) == self.PGA]

        labelGain = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Select gain')
        labelGain.pack(pady=10, padx=10)
        gainMenu = customtkinter.CTkOptionMenu(master, values=gains,
                                                    command=self.select_gain)
        gainMenu.pack(pady=0, padx=10)
        gainMenu.set(gains[int(idx_def[0])])


    def select_gain(self, event):

        self.PGA = int(event)
        print('PGA set to {}'.format(self.PGA))


    def display_samplingrate(self, master):
        
        self.labelSfr = customtkinter.CTkLabel(master=master, 
            justify=customtkinter.LEFT,
            text='Current sampling rate is {} Hz.\nEnter a new one if desired (Hz)'.format(self.sample_rate))
        self.labelSfr.pack(pady=10, padx=10)

        self.textSfr = customtkinter.CTkTextbox(master=master,
                                           width=200, height=15)
        self.textSfr.pack(pady=0, padx=10)
        self.textSfr.insert("0.0", str(self.sample_rate))

        buttonValidate = customtkinter.CTkButton(master=master,
                                                 command=self.select_sampling_rate,
                                                 text='Register new sampl. rate')
        buttonValidate.pack(pady=5, padx=10)


    def select_sampling_rate(self):

        try:
            self.sample_rate = int(self.textSfr.get(0.0, tk.END))
            self.labelSfr.configure(
                text='Current sampling rate is {} Hz.\nEnter a new one if desired (Hz)'.format(self.sample_rate))
            print('Sampling rate set to {}.'.format(self.sample_rate))
        except:
            print('Please enter an integer value. Reverting back to default...')
            self.textSfr.insert("0.0", str(self.sample_rate))


    def display_timerange(self, master):

        labelRange = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Select time range to display')
        labelRange.pack(pady=10, padx=10)
        
        ranges          = [5, 10, 20]
        idx_def         = [i for i in range(len(ranges)) if int(ranges[i]) == self.buffer_length]

        self.range_var = customtkinter.IntVar(value=ranges[int(idx_def[0])])

        for i in range(len(ranges)):
            rb = customtkinter.CTkRadioButton(master=master,
                                              variable=self.range_var,
                                              value=ranges[i],
                                              text=str(ranges[i]) + ' s',
                                              command=self.select_timerange)
            rb.pack(pady=0, padx=10)


    def select_timerange(self):
        
        self.buffer_length = self.range_var.get()
        print('Time range to display set to {} s'.format(self.buffer_length))


    def display_channels(self, master):

        labelChans = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='Channels to display (*))')
        labelChans.pack(pady=10, padx=10)

        self.channels = []
        for i in range(self.max_chans):
            self.channels.append(tk.BooleanVar())
            cb = customtkinter.CTkCheckBox(master=master,
                                            text='Channel ' + str(i+1),
                                            command=self.select_channels,
                                            variable=self.channels[i],
                                            onvalue=True,
                                            offvalue=False)
            cb.select()
            cb.pack(pady=0, padx=10)

        labelInfo = customtkinter.CTkLabel(master=master, 
                                            justify=customtkinter.LEFT,
                                            text='(*) This setting only affects the visualization.\nAll channelswill be processed and stored in output files')
        labelInfo.pack(pady=10, padx=10)


    def select_channels(self):

        for i in range(len(self.channels)):
            if self.selected_chans[i] != self.channels[i].get():
                self.selected_chans[i] = self.channels[i].get()
                if self.channels[i].get():
                    print('Channel {} enabled'.format(i))
                else:
                    print('Channel {} disabled'.format(i))
        

    def on_closing(self):

        self.paramWin.destroy()