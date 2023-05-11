#Prepare userland =========================================================
from backend.Helment_signal_processing      import Processing
from backend.Helment_configure_board        import ConfigureBoard
from backend.Helment_signal_sampling        import Sampling
from backend.Helment_parameter_validation   import ParamVal
from multiprocessing                        import Process, Pipe
from tkinter                                import messagebox
from PIL                                    import Image, ImageTk
from functools                              import partial
from sys                                    import platform
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg      import FigureCanvasTkAgg
import matplotlib.pyplot                    as plt
import numpy                                as np
import tkinter                              as tk
import parameters                           as p


class MainWindow(Processing):

    def __init__(self):

        super(MainWindow, self).__init__()

        # Load parameters
        # -----------------------------------------------------------------
        self.numchans       = p.buffer_channels
        self.numsamples     = int(p.sample_rate * p.buffer_length)
        self.left_edge      = int(p.sample_rate * p.buffer_add)
        self.samplerate     = p.sample_rate
        self.count          = 0
        self.s_down         = p.s_down
        self.idx_retain     = range(0, int(p.sample_rate * p.buffer_length), p.s_down)
        self.yrange         = p.yrange
        self.img_helment    = './backend/Isotipo-Helment-color.png'

        self.get_screen_info()

        # Splash screen
        # -----------------------------------------------------------------
        splash = self.disp_splash()

        # Load methods
        # -----------------------------------------------------------------
        ParamVal()                              # Sanity checks
        confboard           = ConfigureBoard()  # Board communication
        sigproc             = Sampling()        # Signal handling

        # Listen to user input for setting state of board
        # -----------------------------------------------------------------
        splash.update()
        splash.after(0, self.on_start(splash, confboard))

        # Generate variable exchange pipe
        # -----------------------------------------------------------------
        self.recv_conn, self.send_conn = Pipe(duplex = False)

        # Generate separate processes to not slow down sampling by any
        # other executions
        # -----------------------------------------------------------------
        self.sampling    = Process(target=sigproc.fetch_sample,
            args=(self.send_conn, confboard.ser, 
            confboard.av_ports, self.current_state))
        
        if self.current_state == 2 or self.current_state == 3:
            self.sampling.start()

        self.build_frontend()
        self.update_plot_data(self.canvas)


    def build_frontend(self):
        # Build GUI
        # -----------------------------------------------------------------
        self.master = tk.Tk()
        self.master.title('Helment EEG GUI')
        pixels_x, pixels_y          = int(round(0.71*self.screen_width)), int(round(0.8*self.screen_height))
        x_cordinate, y_cordinate    = int((self.screen_width/2) - (pixels_x/2)), int(0)
        self.master.geometry("{}x{}+{}+{}".format(pixels_x, pixels_y, x_cordinate, y_cordinate))
        # self.master.iconphoto(False, ImageTk.PhotoImage(file=self.img_helment))
        self.master.lift()
        self.master.attributes("-topmost", True)
        self.master.after_idle(self.master.attributes, '-topmost', False)
        
        # multiple image size by zoom
        pixels_x, pixels_y = tuple([int(0.01 * x) for x in Image.open(self.img_helment).size])
        img = ImageTk.PhotoImage(Image.open(self.img_helment).resize((pixels_x, pixels_y)))
        self.frameLogo = tk.Label(self.master, image=img, bg='#dddddd')
        self.frameLogo.image = img
        self.frameLogo.grid(row=1, column=1)
        self.frameLogo = tk.LabelFrame(self.frameLogo, text='Logo',
            padx=0, pady=0)
                    
        self.frameYRange = tk.Label(self.master, bg='#dddddd')
        self.frameYRange.grid(row=1, column=2)
        self.frameYRange = tk.LabelFrame(self.frameYRange, text='Vert. range (uV)',
            padx=0, pady=0)
        
        self.frameVDisp  = tk.Label(self.master, bg='#dddddd')
        self.frameVDisp.grid(row=1, column=3)
        self.frameVDisp  = tk.LabelFrame(self.frameVDisp, text='Maximum (uV)',
            padx=0, pady=0)

        self.frameNotch = tk.Label(self.master, bg='#dddddd')
        self.frameNotch.grid(row=1, column=4)
        self.frameNotch = tk.LabelFrame(self.frameNotch, text='Notch filter',
            padx=0, pady=0)

        self.frameBandpass = tk.Label(self.master, bg='#dddddd')
        self.frameBandpass.grid(row=1, column=5)
        self.frameBandpass = tk.LabelFrame(self.frameBandpass, text='Bandpass (Hz)',
            padx=0, pady=0)

        self.frameEnvelope = tk.Label(self.master, bg='#dddddd')
        self.frameEnvelope.grid(row=1, column=6)
        self.frameEnvelope = tk.LabelFrame(self.frameEnvelope, text='Display envelope',
            padx=0, pady=0)

        self.frameStream = tk.Label(self.master, bg='#dddddd')
        self.frameStream.grid(row=1, column=7)
        self.frameStream = tk.LabelFrame(self.frameStream, text='Start/Stop data stream',
            padx=0, pady=0)

        self.frameSignal = tk.Label(self.master, bg='#dddddd')
        self.frameSignal.grid(row=2, column=1, columnspan=7)
        self.frameSignal = tk.LabelFrame(self.frameSignal, text='Data stream',
            padx=0, pady=0)

        # Define inputs from GUI elements
        notch           = tk.IntVar()
        bpass           = tk.StringVar()
        yran            = tk.StringVar()
        self.currran    = tk.StringVar()
        self.currran.set('c1: ' + str(round(self.yrange[1])) + '\nc2: ' + str(round(self.yrange[1])))
        self.stream     = tk.StringVar()
        self.stream.set('Stop')
        self.streaming  = True
        self.envelope   = False
        self.bSB        = self.b_notch
        self.aSB        = self.a_notch
        self.bPB        = self.b_wholerange
        self.aPB        = self.a_wholerange
        envelope        = tk.BooleanVar()

        tk.Radiobutton(self.frameYRange, text='100',
            variable=yran, value=100,
            command=partial(self.yrange_selection, yran)).grid(row=1, column=1)
        tk.Radiobutton(self.frameYRange, text='200',
            variable=yran, value=200,
            command=partial(self.yrange_selection, yran)).grid(row=1, column=2)
        tk.Radiobutton(self.frameYRange, text='500',
            variable=yran, value=500,
            command=partial(self.yrange_selection, yran)).grid(row=1, column=3)
        tk.Radiobutton(self.frameYRange, text='1000',
            variable=yran, value=1000,
            command=partial(self.yrange_selection, yran)).grid(row=1, column=4)
        tk.Radiobutton(self.frameYRange, text='Auto',
            variable=yran, value='Auto',
            command=partial(self.yrange_selection, yran)).grid(row=1, column=5)
        self.frameYRange.grid(row=1, columnspan=1, padx= 0)

        tk.Label(self.frameVDisp, textvariable=self.currran).grid(row=1, column=1)
        self.frameVDisp.grid(row=1, columnspan=1, padx= 0)
        

        tk.Radiobutton(self.frameNotch, text='50 Hz',
            variable=notch, value=50,
            command=partial(self.filt_selection, notch)).grid(row=1, column=1)
        tk.Radiobutton(self.frameNotch, text='60 Hz',
            variable=notch, value=60,
            command=partial(self.filt_selection, notch)).grid(row=1, column=2)
        tk.Radiobutton(self.frameNotch, text='Off',
            variable=notch, value=0,
            command=partial(self.filt_selection, notch)).grid(row=1, column=3)
        self.frameNotch.grid(row=1, columnspan=1, padx=0)

        tk.Radiobutton(self.frameBandpass, text='0.5 - 45', 
            variable=bpass, value='whole',
            command=partial(self.filt_selection, bpass)).grid(row=1, column=1)
        tk.Radiobutton(self.frameBandpass, text='1 - 30',
            variable=bpass, value='sleep',
            command=partial(self.filt_selection, bpass)).grid(row=1, column=2)
        tk.Radiobutton(self.frameBandpass, text='4 - 8',
            variable=bpass, value='theta',
            command=partial(self.filt_selection, bpass)).grid(row=1, column=3)
        self.frameBandpass.grid(row=1, columnspan=1, padx=0)

        tk.Radiobutton(self.frameEnvelope, text='Off', 
            variable=envelope, value=False,
            command=partial(self.disp_envelope, envelope)).grid(row=1, column=1)
        tk.Radiobutton(self.frameEnvelope, text='On',
            variable=envelope, value=True,
            command=partial(self.disp_envelope, envelope)).grid(row=1, column=2)
        self.frameEnvelope.grid(row=1, columnspan=1, padx=0)

        tk.Button(self.frameStream, textvariable=self.stream, command=self.streamstate).pack()
        self.frameStream.pack()

        self.x = list(range(-self.numsamples, 0, self.s_down))
        self.x = [x/self.samplerate for x in self.x]
        self.y = []
        for _ in range(self.numchans):
            self.y.append([0 for _ in range(0, self.numsamples, self.s_down)])

        self.fig, self.ax   = plt.subplots(self.numchans, 1,
            figsize=(self.screen_width*0.7/80, self.screen_height*0.7/80), dpi=80)
        self.fig.tight_layout() # Reduce whitespace of the figure

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frameSignal)
        plot_widget = self.canvas.get_tk_widget()
        plot_widget.grid(row=0, column=0)
        self.frameSignal.grid(row=0, column=0, columnspan=5)


    def update_plot_data(self, canvas):

        sampleplot      = {}
        for iChan in range(self.numchans):
            if iChan == 0:
                self.ax[iChan].set_title('Time (s)')
            sampleplot[iChan], = self.ax[iChan].plot(
                self.x, self.y[iChan], linestyle='None', animated=True)
            self.ax[iChan].set_ylabel('Amp. (uV)')
            self.ax[iChan].set_ylim(
                bottom = self.yrange[0],
                top = self.yrange[1],
                emit = False, auto = False)
            self.ax[iChan].set_ymargin(0) # Expand signal to vertical edges

            x0          = self.x[0]
            xend        = self.x[-1]
            xrange      = range(int(round(x0, 0)), int(round(xend, 0)), 1)
            self.ax[iChan].set_xticks([])
            self.ax[iChan].set_xlim((x0, xend))
            self.ax[iChan].set_xmargin(0) # Expand signal to horizontal edges
            self.ax[iChan].grid(visible=1, which='major', axis='both', 
                linestyle=':', alpha=0.5)

        for iChan in range(self.numchans):
            sampleplot[iChan].set_linestyle('-')
            self.ax[iChan].set_xticks(xrange)
            if iChan == self.numchans-1:
                self.ax[iChan].set_xticklabels(xrange)
            else:
                self.ax[iChan].set_xticklabels([])
            self.ax[iChan].set_yticks([
                self.yrange[0],
                self.yrange[0]/2,
                0,
                self.yrange[1]/2,
                self.yrange[1]])
            self.ax[iChan].set_yticklabels([])
        canvas.draw()

        # get copy of entire figure (everything inside fig.bbox) sans animated artist
        bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)

        # draw the animated artist, this uses a cached renderer
        for iChan in range(self.numchans):
            self.ax[iChan].draw_artist(sampleplot[iChan])

        # show the result to the screen, this pushes the updated RGBA buffer from the
        # renderer to the GUI framework so you can see it
        self.fig.canvas.blit(self.fig.bbox)

        vrange = [self.yrange[1], self.yrange[1]]

        while not self.recv_conn.closed: # Update plots for every channel

            buffer, t_now   = self.recv_conn.recv()

            self.count = self.count + 1
            if self.count < self.s_down:
                continue

            # Filter buffer signal and send filtered data to plotting funcs
            # -------------------------------------------------------------
            processed_buffer    = self.prepare_buffer(buffer, 
                self.bSB, self.aSB, self.bPB, self.aPB)
            processed_buffer    = processed_buffer[:, self.left_edge:]

            if self.envelope == True:
                processed_buffer = self.extract_envelope(processed_buffer)

            self.x          = self.x[1:]  # Remove the first y element
            self.x.append(self.x[-1]+self.count/self.samplerate) # t_now/1000

            if self.streaming == True:
                xdata           = self.x
                x0              = xdata[0]
                xend            = xdata[-1]
                xrange          = range(int(round(x0, 0)), int(round(xend, 0)), 1)
            
            # reset the background back in the canvas state, screen unchanged
            self.fig.canvas.restore_region(bg)

            # Update plots for every channel
            # -------------------------------------------------------------
            for iChan in range(self.numchans):
                if self.streaming == True:
                    self.y[iChan] = processed_buffer[iChan, self.idx_retain]

                sampleplot[iChan].set_ydata(self.y[iChan]) # Y values

                # Move x axis the friendly way
                sampleplot[iChan].set_xdata(xdata)
                self.ax[iChan].set_xticks(xrange)
                if iChan == self.numchans-1:
                    self.ax[iChan].set_xticklabels(xrange)
                self.ax[iChan].set_xlim((x0, xend))

                # Set vertical range
                if self.yrange == None:
                    extr_val = np.max([
                        np.abs(np.min(self.y[iChan])),
                        np.abs(np.max(self.y[iChan]))])
                    self.ax[iChan].set_ylim((-extr_val, extr_val))
                    vrange[iChan] = round(extr_val)
                else:
                    self.ax[iChan].set_ylim(self.yrange)
                    vrange[iChan] = round(self.yrange[1])

                # re-render the artist, updating the canvas state, but not the screen
                self.ax[iChan].draw_artist(sampleplot[iChan])
                # The below line updates the x-axis but is slowing down the code a lot
                # self.ax[iChan].draw_artist(self.ax[iChan])

            # Display current signal amplitude in time window
            self.update_disp_vrange(self.currran, vrange)

            # Update plot time stamp and figure
            # -------------------------------------------------------------
            # copy the image to the GUI state, but screen might not be changed yet
            self.fig.canvas.blit(self.fig.bbox)
            # flush any pending GUI events, re-painting the screen if needed
            self.fig.canvas.flush_events()
            self.count          = 0


    def filt_selection(self, button):
        choice = button.get()
        choice = str(choice)
        if choice == '50':
            print('Enabled 50 Hz stopband filter')
            self.bSB    = self.b_notch
            self.aSB    = self.a_notch
        elif choice == '60':
            print('Enabled 60 Hz stopband filter')
            self.bSB    = self.b_notch60
            self.aSB    = self.a_notch60
        elif choice == '0':
            print('Notch filter disabled')
            self.bSB    = np.array([None, None]) # Avoiding bool not iterable
            self.aSB    = np.array([None, None])
        elif choice == 'whole':
            print('Bandpass filter between 0.1 and 45 Hz')
            self.bPB        = self.b_wholerange
            self.aPB        = self.a_wholerange
        elif choice == 'sleep':
            print('Bandpass filter between 1 and 30 Hz')
            self.bPB        = self.b_sleep
            self.aPB        = self.a_sleep
        elif choice == 'theta':
            print('Bandpass filter between 4 and 8 Hz')
            self.bPB        = self.b_theta
            self.aPB        = self.a_theta


    def yrange_selection(self, button):
        choice = button.get()
        choice = str(choice)
        if choice == '100':
            print('Vertical range set to -100 uV to +100 uV')
            self.yrange = (-100, 100)
        elif choice == '200':
            print('Vertical range set to -200 uV to +200 uV')
            self.yrange = (-200, 200)
        elif choice == '500':
            print('Vertical range set to -500 uV to +500 uV')
            self.yrange = (-500, 500)
        elif choice == '1000':
            print('Vertical range set to -1000 uV to +1000 uV')
            self.yrange = (-1000, 1000)
        elif choice == 'Auto':
            print('Vertical range set relative to signal')
            self.yrange = None


    def update_disp_vrange(self, target, values):
        target.set('c1: ' + str(values[0]) + '\nc2: ' + str(values[1]))


    def disp_envelope(self, button):
        choice = button.get()
        if choice == True:
            print('Enabled envelope displaying')
            self.envelope = True
        elif choice == False:
            print('Disabled envelope displaying')
            self.envelope = False


    def streamstate(self):
        if self.stream.get() == 'Start':
            self.stream.set('Stop')
            self.streaming = True
        elif self.stream.get() == 'Stop':
            self.stream.set('Start')
            self.streaming = False


    def get_screen_info(self):
        root = tk.Tk()
        # Get information about screen to center the windows
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()


    def disp_splash(self):
        root = tk.Tk()

        # multiple image size by zoom
        pixels_x, pixels_y = tuple([int(0.10 * x) for x in Image.open(self.img_helment).size])
        img = ImageTk.PhotoImage(Image.open(self.img_helment).resize((pixels_x, pixels_y)))

        x_cordinate = int((self.screen_width/2) - (pixels_x/2))
        y_cordinate = int((self.screen_height/2) - (pixels_y/2))

        root.geometry("{}x{}+{}+{}".format(pixels_x, pixels_y, x_cordinate, y_cordinate))

        if platform == "linux" or platform == "linux2":
            root.overrideredirect(True)
            root.wait_visibility(root)
            root.wm_attributes("-alpha", 0.5)
        elif platform == "darwin":
            root.overrideredirect(True)
            # Make the root window always on top
            root.wm_attributes("-topmost", True)
            # Turn off the window shadow
            root.wm_attributes("-transparent", True)
            # Set the root window background color to a transparent color
            root.config(bg='systemTransparent')
            # Store the PhotoImage to prevent early garbage collection
            root.image = img
            # Display the image on a label
            label = tk.Label(root, image=root.image)
            # Set the label background color to a transparent color
            label.config(bg='systemTransparent')
            label.pack()
        elif platform == "win32":
            root.image = img
            label = tk.Label(root, image=root.image, bg='white')
            root.overrideredirect(True)
            root.lift()
            root.wm_attributes("-topmost", True)
            root.wm_attributes("-disabled", True)
            root.wm_attributes("-transparentcolor", "white")
            label.pack()

        return root


    def on_start(self, win, config):
        self.current_state = -1 # Value that does nothing
        print('Waiting for input: Numerical key stroke...')
        while True:
            self.current_state = config.query_input()
            if self.current_state == 2 or self.current_state == 3:
                win.destroy()
                break


    def on_closing(self):
        # Currently not working for unknown reason
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.master.destroy()


if __name__ == '__main__': # Necessary line for "multiprocessing" to work
    
    sigplots                = MainWindow()  # Contains all necessary bits
