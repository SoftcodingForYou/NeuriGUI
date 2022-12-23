from tkinter                                import *
from tkinter                                import messagebox
from functools                              import partial
from pyqtgraph                              import PlotWidget, plot
import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg      import FigureCanvasTkAgg
import matplotlib.pyplot                    as plt
import numpy                                as np


#Prepare userland =========================================================
import parameters                           as p
from backend.Helment_signal_processing      import Processing
from backend.Helment_configure_board        import ConfigureBoard
from backend.Helment_signal_sampling        import Sampling
from backend.Helment_parameter_validation   import ParamVal
from multiprocessing                        import Process, Pipe


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

        # Load methods
        # -----------------------------------------------------------------
        ParamVal()                              # Sanity checks
        confboard           = ConfigureBoard()  # Board communication
        sigproc             = Sampling()        # Signal handling

        # Listen to user input for setting state of board
        # -----------------------------------------------------------------
        current_state = -1 # Value that does nothing
        print('Waiting for input: Numerical key stroke...')
        while True:
            current_state = confboard.query_input()
            if current_state == 2 or current_state == 3:
                break

        # Generate variable exchange pipe
        # -----------------------------------------------------------------
        self.recv_conn, self.send_conn = Pipe(duplex = False)

        # Generate separate processes to not slow down sampling by any
        # other executions
        # -----------------------------------------------------------------
        self.sampling    = Process(target=sigproc.fetch_sample,
            args=(self.send_conn, confboard.ser, 
            confboard.av_ports, current_state))
        
        if current_state == 2 or current_state == 3:
            self.sampling.start()

        # Build GUI
        # -----------------------------------------------------------------
        self.master = Tk()
        self.master.title('EEG GUI')
        self.master.geometry('1600x900')

        self.frame1 = Label(self.master, bg='#dddddd')
        self.frame1.grid(row=1, column=1)
        self.frame1 = LabelFrame(self.frame1, text='Notch filter', padx=30, pady=10)

        self.frame2 = Label(self.master, bg='#dddddd')
        self.frame2.grid(row=1, column=2)
        self.frame2 = LabelFrame(self.frame2, text='Bandpass (Hz)', padx=30, pady=10)

        self.frame3 = Label(self.master, bg='#dddddd')
        self.frame3.grid(row=1, column=3)
        self.frame3 = LabelFrame(self.frame3, text='Start/Stop data stream', padx=10, pady=10)

        self.frame4 = Label(self.master, bg='#dddddd')
        self.frame4.grid(row=2, column=1, columnspan=3)
        self.frame4 = LabelFrame(self.frame4, text='Data stream', padx=70, pady=70)

        # Define inputs from GUI elements
        notch           = IntVar()
        bpass           = StringVar()
        self.stream     = StringVar()
        self.stream.set('Stop')
        self.streaming  = True
        self.bSB        = self.b_notch
        self.aSB        = self.a_notch
        self.bPB        = self.b_wholerange
        self.aPB        = self.a_wholerange

        Radiobutton(self.frame1, text='50 Hz', variable=notch, value=50,command=partial(self.selection, notch)).grid(row=1, column=1)
        Radiobutton(self.frame1, text='60 Hz', variable=notch, value=60,command=partial(self.selection, notch)).grid(row=1, column=2)
        Radiobutton(self.frame1, text='Off', variable=notch, value=0,command=partial(self.selection, notch)).grid(row=1, column=3)
        self.frame1.grid(row=1, columnspan=1, padx=90)

        Radiobutton(self.frame2, text='0.5 - 45', variable=bpass, value='whole',command=partial(self.selection, bpass)).grid(row=1, column=1)
        Radiobutton(self.frame2, text='1 - 30', variable=bpass, value='sleep',command=partial(self.selection, bpass)).grid(row=1, column=2)
        Radiobutton(self.frame2, text='4 - 8', variable=bpass, value='theta',command=partial(self.selection, bpass)).grid(row=1, column=3)
        self.frame2.grid(row=1, columnspan=1, padx=90)

        btn = Button(self.frame3, textvariable=self.stream, command=self.streamstate).pack()
        self.frame3.pack()

        self.x = list(range(-self.numsamples, 0, self.s_down))
        self.x = [x/self.samplerate for x in self.x]
        self.y = []
        for _ in range(self.numchans):
            self.y.append([0 for _ in range(0, self.numsamples, self.s_down)])

        self.fig, self.ax   = plt.subplots(self.numchans, 1,
            figsize=(15, 8), dpi=80)

        canvas = FigureCanvasTkAgg(self.fig, master=self.frame4)
        plot_widget = canvas.get_tk_widget()
        plot_widget.grid(row=2, column=0)
        self.frame4.grid(row=0, column=0, columnspan=3)

        self.update_plot_data()


    def update_plot_data(self):

        sampleplot      = {}
        for iChan in range(self.numchans):
            if iChan == 0:
                self.ax[iChan].set_title('Helment')
            elif iChan == self.numchans - 1:
                self.ax[iChan].set_xlabel('Time (s)')
            sampleplot[iChan], = self.ax[iChan].plot(self.x, self.y[iChan])
            self.ax[iChan].set_ylabel('Amp. (uV)')
            self.ax[iChan].set_ylim(
                bottom = self.yrange[0],
                top = self.yrange[1],
                emit = False, auto = False)
            self.ax[iChan].set_xticks(
                range(int(round(self.x[0], 0)), 
                int(round(self.x[-1]+1, 0)), 1))
            # self.ax[iChan].set_xticklabels([])
            self.ax[iChan].set_xmargin(0) # Expand signal to vertical edges
            self.ax[iChan].grid(visible=1, which='major', axis='both', linestyle=':', alpha=0.5)
        plt.show(block=False)
        plt.pause(1)

        # get copy of entire figure (everything inside fig.bbox) sans animated artist
        bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)
        # draw the animated artist, this uses a cached renderer
        for iChan in range(self.numchans):
            self.ax[iChan].draw_artist(sampleplot[iChan])

        # show the result to the screen, this pushes the updated RGBA buffer from the
        # renderer to the GUI framework so you can see it
        self.fig.canvas.blit(self.fig.bbox)

        plt.close() # Closes unnecessary window

        while not self.recv_conn.closed: # Update plots for every channel
            # -----------------------------------------------------------------
            buffer, t_now   = self.recv_conn.recv()

            self.count = self.count + 1
            if self.count < self.s_down:
                continue

            # Filter buffer signal and send filtered data to plotting funcs
            # -------------------------------------------------------------
            processed_buffer    = self.prepare_buffer(buffer, 
                self.bSB, self.aSB, self.bPB, self.aPB)
            processed_buffer    = processed_buffer[:, self.left_edge:]

            self.x              = self.x[1:]  # Remove the first y element
            self.x.append(self.x[-1]+self.count/self.samplerate) # t_now/1000
            
            # reset the background back in the canvas state, screen unchanged
            self.fig.canvas.restore_region(bg)

            # Update plots for every channel
            # -------------------------------------------------------------
            for iChan in range(self.numchans):
                if self.streaming == True:
                    self.y[iChan] = processed_buffer[iChan, self.idx_retain]

                sampleplot[iChan].set_ydata(self.y[iChan]) # Y values
                # re-render the artist, updating the canvas state, but not the screen
                self.ax[iChan].draw_artist(sampleplot[iChan])

            # Update plot time stamp and figure
            # -------------------------------------------------------------
            # copy the image to the GUI state, but screen might not be changed yet
            self.fig.canvas.blit(self.fig.bbox)
            # flush any pending GUI events, re-painting the screen if needed
            self.fig.canvas.flush_events()
            self.count          = 0


    def selection(self, button):
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


    def streamstate(self):
        if self.stream.get() == 'Start':
            self.stream.set('Stop')
            self.streaming = True
        elif self.stream.get() == 'Stop':
            self.stream.set('Start')
            self.streaming = False


    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.master.destroy()


if __name__ == '__main__': # Necessary line for "multiprocessing" to work
    
    sigplots                = MainWindow()  # Contains all necessary bits