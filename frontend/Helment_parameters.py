import tkinter                              as tk
from tkinter                                import messagebox, ttk
from functools                              import partial
from PIL                                    import Image, ImageTk
import serial.tools.list_ports

class Parameters:

    def __init__(self):

        super(Parameters, self).__init__()

        self.set_defaults()
        self.img_helment    = './frontend/Isotipo-Helment-color.png'

        self.get_screen_info()
        self.build_frontend()

        self.master.mainloop()


    def set_defaults(self):

        #Session-specific parameters
        self.yrange         = [-1000, 1000] # List of scalars ([negative, positive]) in order to set figure y axis range
        self.notch          = 0 # Integer 0 (Off), 50 (50 Hz) or 60 (60 Hz)
        self.bpass          = 0 # Integer -1 to 3 according to number of options in "frequency_bands" below
        self.dispenv        = False # Boolean 0 (Off), 1 (On)

        #Signal arrays
        self.sample_rate    = 200 #Hertz
        self.buffer_channels= 2 #scalar
        self.buffer_length  = 20 #scalar (seconds)
        self.buffer_add     = 4 #scalar (seconds), we add this to the buffer for filtering to avoid edge artifacts
        self.sample_count   = 0 #integer zero
        self.saving_interval= 1 #scalar (seconds)
        self.PGA            = 24 #scalar

        #Signal reception
        self.baud_rate      = 115200 #scalar default baudrate for connection
        self.port           = '' #Leave blank
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
        self.master = tk.Tk()
        self.master.title('Settings (close when ready)')
        pixels_x, pixels_y          = int(round(0.71*self.screen_width)), int(round(0.8*self.screen_height))
        x_cordinate, y_cordinate    = int((self.screen_width/2) - (pixels_x/2)), int(0)
        # self.master.geometry("{}x{}+{}+{}".format(pixels_x, pixels_y, x_cordinate, y_cordinate))
        # self.master.iconphoto(False, ImageTk.PhotoImage(file=self.img_helment))
        self.master.lift()
        self.master.attributes("-topmost", True)
        self.master.after_idle(self.master.attributes, '-topmost', False)

        # Set closing sequence
        # -----------------------------------------------------------------
        # Just closing the window makes the sampling process hang. We 
        # prevent this by setting up a protocol.
        self.master.protocol('WM_DELETE_WINDOW', self.on_closing)

        self.padx = 25
        self.pady = 15

        self.display_logo()
        self.display_ports()
        self.display_gains()
        self.display_timerange()
        
    
    def get_screen_info(self):

        root = tk.Tk()
        # Get information about screen to center the windows
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()


    def display_logo(self):

        # multiple image size by zoom
        pixels_x, pixels_y = tuple([int(0.01 * x) for x in Image.open(self.img_helment).size])
        img = ImageTk.PhotoImage(Image.open(self.img_helment).resize((pixels_x, pixels_y)), master=self.master)
        self.frameLogo = tk.Label(self.master, image=img)
        self.frameLogo.image = img
        self.frameLogo.grid(row=1, column=1, padx=self.padx, pady=self.pady)


    def display_ports(self):

        ports = list(serial.tools.list_ports.comports())
        portvar = tk.Variable(value=[port.name for port in ports])

        lf = ttk.LabelFrame(self.master, text='Port')
        lf.grid(row=1, column=2, padx=self.padx, pady=self.pady)

        self.portlist = tk.Listbox(
            master=lf,
            listvariable=portvar,
            height=12,
            selectmode=tk.SINGLE)
        self.portlist.pack()

        # Update port upon selection
        self.portlist.bind('<<ListboxSelect>>', self.select_port)


    def select_port(self, event):

        selected_idx    = self.portlist.curselection()
        self.port       = ''.join(self.portlist.get(selected_idx))
        print('Selected port {}'.format(self.port))


    def display_gains(self):

        gains = ['2', '4', '8', '24']
        idx_def = [i for i in range(len(gains)) if int(gains[i]) == self.PGA]

        lf = ttk.LabelFrame(self.master, text='PGA (gain)')
        lf.grid(row=1, column=3, padx=self.padx, pady=self.pady)

        self.gainlist = ttk.Combobox(
            master=lf,
            state="readonly",
            values=gains,
            height=12)
        self.gainlist.current(idx_def)
        self.gainlist.pack()

        # Update port upon selection
        self.gainlist.bind('<<ComboboxSelected>>', self.select_gain)


    def select_gain(self, event):

        self.PGA = self.gainlist.get()
        print('Selected PGA {}'.format(self.PGA))


    def display_timerange(self):

        lf = ttk.LabelFrame(self.master, text='Time range (s)')
        lf.grid(row=1, column=4, padx=self.padx, pady=self.pady)

        self.trangeint = tk.IntVar()
        self.timerangeval = tk.Entry(
            master=lf,
            validate='all',
            textvariable=self.trangeint)
        self.timerangeval.insert("end", 'Default: 20')
        self.timerangeval.pack()

        valbutton = ttk.Button(lf, text="Validate", command=self.select_timerange)
        valbutton.pack(fill='x', expand=True, pady=10)


    def select_timerange(self):
        try:
            self.buffer_length = self.trangeint.get()
        except:
            print('/!\\ Expected an integer number. Reverting to default value (20 s)')
        print('Selected time range to display {} s'.format(self.buffer_length))


    def on_closing(self):

        self.master.destroy()