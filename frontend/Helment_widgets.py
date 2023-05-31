#Prepare userland =========================================================
import parameters                           as p
from backend.Helment_signal_processing      import Processing
from PyQt5                                  import QtCore, QtWidgets
from pyqtgraph                              import PlotWidget
from functools                              import partial
import pyqtgraph                            as pg
import numpy                                as np

class GUIWidgets(Processing):

    def __init__(self):

        super(GUIWidgets, self).__init__() # Init Processing class first

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
        self.notch          = p.notch
        self.bpass          = p.bpass
        self.denv           = p.dispenv
        self.img_helment    = './frontend/Isotipo-Helment-color.png'

        # Defaults
        self.streaming      = True
        self.envelope       = False
        self.bSB            = self.b_notch
        self.aSB            = self.a_notch
        self.bPB            = self.b_wholerange
        self.aPB            = self.a_wholerange


    def fg_vert_range(self):
        # -----------------------------------------------------------------
        # Vert. range (uV)
        # rbt1 (Auto) rdbt2 (100) rdbt3 (200) rdbt4 (500) rdbt5 (1000)
        # -----------------------------------------------------------------
        vert_range          = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()
        horilayout          = QtWidgets.QHBoxLayout()
        title               = QtWidgets.QLabel('Vert. range (uV)')
        rbtn1               = QtWidgets.QRadioButton('Auto')
        rbtn2               = QtWidgets.QRadioButton('100')
        rbtn3               = QtWidgets.QRadioButton('200')
        rbtn4               = QtWidgets.QRadioButton('500')
        rbtn5               = QtWidgets.QRadioButton('1000')
        
        if self.yrange[1] == 0:
            rbtn1.setChecked(True)
        elif self.yrange[1] == 100:
            rbtn2.setChecked(True)
        elif self.yrange[1] == 200:
            rbtn3.setChecked(True)
        elif self.yrange[1] == 500:
            rbtn4.setChecked(True)
        elif self.yrange[1] == 1000:
            rbtn5.setChecked(True)

        rbtn1.clicked.connect(lambda: self.yrange_selection(0))
        rbtn2.clicked.connect(lambda: self.yrange_selection(100))
        rbtn3.clicked.connect(lambda: self.yrange_selection(200))
        rbtn4.clicked.connect(lambda: self.yrange_selection(500))
        rbtn5.clicked.connect(lambda: self.yrange_selection(1000))

        vertlayout.addWidget(title)
        vertlayout.addLayout(horilayout)
        horilayout.addWidget(rbtn1)
        horilayout.addWidget(rbtn2)
        horilayout.addWidget(rbtn3)
        horilayout.addWidget(rbtn4)
        horilayout.addWidget(rbtn5)
        vert_range.setLayout(vertlayout)

        return vert_range
    

    def fg_notch_filter(self):
        # -----------------------------------------------------------------
        # Notch filter
        # rbt1 (50 Hz) rdbt2 (60 Hz) rdbt3 (Off)
        # -----------------------------------------------------------------
        notch_filter        = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()
        horilayout          = QtWidgets.QHBoxLayout()
        title               = QtWidgets.QLabel('Notch filter (Hz)')
        rbtn1               = QtWidgets.QRadioButton('50')
        rbtn2               = QtWidgets.QRadioButton('60')
        rbtn3               = QtWidgets.QRadioButton('Off')

        if self.notch == 50:
            rbtn1.setChecked(True)
        elif self.notch == 60:
            rbtn2.setChecked(True)
        elif self.notch == 0:
            rbtn3.setChecked(True)

        rbtn1.clicked.connect(lambda: self.filt_noise(50))
        rbtn2.clicked.connect(lambda: self.filt_noise(60))
        rbtn3.clicked.connect(lambda: self.filt_noise(0))

        vertlayout.addWidget(title)
        vertlayout.addLayout(horilayout)
        horilayout.addWidget(rbtn1)
        horilayout.addWidget(rbtn2)
        horilayout.addWidget(rbtn3)
        notch_filter.setLayout(vertlayout)

        return notch_filter
    

    def fg_bandpass_filter(self):
        # -----------------------------------------------------------------
        # Bandpass (Hz)
        # rbt1 (0.5 - 45) rdbt2 (1 - 30) rdbt3 (4 - 8)
        # -----------------------------------------------------------------
        bandpass_filter     = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()
        horilayout          = QtWidgets.QHBoxLayout()
        title               = QtWidgets.QLabel('Bandpass (Hz)')
        rbtn1               = QtWidgets.QRadioButton('Raw')
        rbtn2               = QtWidgets.QRadioButton('Detrend')
        rbtn3               = QtWidgets.QRadioButton('0.5 - 45')
        rbtn4               = QtWidgets.QRadioButton('1 - 30')
        rbtn5               = QtWidgets.QRadioButton('4 - 8')

        if self.bpass == -1:
            rbtn1.setChecked(True)
        elif self.bpass == 0:
            rbtn2.setChecked(True)
        elif self.bpass == 1:
            rbtn3.setChecked(True)
        elif self.bpass == 2:
            rbtn4.setChecked(True)
        elif self.bpass == 3:
            rbtn5.setChecked(True)

        rbtn1.clicked.connect(lambda: self.filt_bandpass(-1))
        rbtn2.clicked.connect(lambda: self.filt_bandpass(0))
        rbtn3.clicked.connect(lambda: self.filt_bandpass(1))
        rbtn4.clicked.connect(lambda: self.filt_bandpass(2))
        rbtn5.clicked.connect(lambda: self.filt_bandpass(3))

        vertlayout.addWidget(title)
        vertlayout.addLayout(horilayout)
        horilayout.addWidget(rbtn1)
        horilayout.addWidget(rbtn2)
        horilayout.addWidget(rbtn3)
        horilayout.addWidget(rbtn4)
        horilayout.addWidget(rbtn5)
        bandpass_filter.setLayout(vertlayout)

        return bandpass_filter
    

    def fg_envelope(self):
        # -----------------------------------------------------------------
        # Display envelope
        # rbt1 (Off) rdbt2 (On)
        # -----------------------------------------------------------------
        envelope            = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()
        horilayout          = QtWidgets.QHBoxLayout()
        title               = QtWidgets.QLabel('Display envelope')
        rbtn1               = QtWidgets.QRadioButton('Off')
        rbtn2               = QtWidgets.QRadioButton('On')

        if self.denv == False:
            rbtn1.setChecked(True)
        elif self.denv == True:
            rbtn2.setChecked(True)

        rbtn1.clicked.connect(lambda: self.disp_envelope(False))
        rbtn2.clicked.connect(lambda: self.disp_envelope(True))

        vertlayout.addWidget(title)
        vertlayout.addLayout(horilayout)
        horilayout.addWidget(rbtn1)
        horilayout.addWidget(rbtn2)
        envelope.setLayout(vertlayout)

        return envelope
    

    def fg_stream_button(self):
        # -----------------------------------------------------------------
        # Data stream
        # Dynamic button (Start/Stop (default))
        # -----------------------------------------------------------------
        stream              = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()
        title               = QtWidgets.QLabel('Data stream')
        self.streambtn      = QtWidgets.QPushButton(text="Started")

        self.streambtn.clicked.connect(self.streamstate)

        vertlayout.addWidget(title)
        vertlayout.addWidget(self.streambtn)
        stream.setLayout(vertlayout)
        
        return stream
    

    def fg_signal_stream(self):
        signal              = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()

        self.x              = list(range(-self.numsamples, 0, self.s_down))
        self.x              = [x/self.samplerate for x in self.x]
        self.y              = [0 for _ in range(0, self.numsamples, self.s_down)]
        self.data_line      = {}

        for iChan in range(self.numchans):

            signalgraph     = PlotWidget()

            # Aesthetics
            signalgraph.setBackground('w')
            signalgraph.setLabel('left', 'Amplitude (uV)')
            signalgraph.setLabel('bottom', 'Time (s)')
            signalgraph.showGrid(x=True, y=True)
            pen1 = pg.mkPen(color=(49,130,189), width=1)
            
            # Decorate plot
            signalgraph.addLegend()
            signalgraph.setAntialiasing(False)
            signalgraph.setYRange(p.yrange[0], p.yrange[1])
            signalgraph.setRange(yRange=(p.yrange[0], p.yrange[1]), disableAutoRange=True)
            
            # Set signal lines
            self.data_line[iChan] =  signalgraph.plot(self.x, self.y, name='Channel {}'.format(str(iChan+1)), pen=pen1)

            vertlayout.addWidget(signalgraph)

        signal.setLayout(vertlayout)

        return signal


    def update_signal_plot(self, recv_conn):

        # Update plots for every channel
        # -----------------------------------------------------------------
        buffer, t_now   = recv_conn.recv()

        self.count = self.count + 1
        if self.count < self.s_down:
            return

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
        

        # Update plots for every channel
        # -------------------------------------------------------------
        for iChan in range(self.numchans):
            if self.streaming == True:
                self.y = processed_buffer[iChan, self.idx_retain]
                self.data_line[iChan].setData(self.x, self.y)  # Update the data

            # Set vertical range
            if self.yrange[1] == 0:
                vscale = [-np.max([np.abs(np.min(self.y[iChan])), np.abs(np.max(self.y[iChan]))]),
                            np.max([np.abs(np.min(self.y[iChan])), np.abs(np.max(self.y[iChan]))])]
            else:
                vscale = self.yrange

            # if self.envelope == True:
            #     self.ax[iChan].set_ylim([0, vscale[1]])
            # else:
            #     self.ax[iChan].set_ylim(vscale)

        self.count          = 0

    
    def filt_noise(self, choice):
        choice = int(choice)
        if choice == 50:
            print('Enabled 50 Hz stopband filter')
            self.bSB    = self.b_notch
            self.aSB    = self.a_notch
        elif choice == 60:
            print('Enabled 60 Hz stopband filter')
            self.bSB    = self.b_notch60
            self.aSB    = self.a_notch60
        elif choice == 0:
            print('Notch filter disabled')
            self.bSB    = np.array([None, None]) # Avoiding bool not iterable
            self.aSB    = np.array([None, None])


    def filt_bandpass(self, choice):
        choice = int(choice)
        if choice == -1:
            print('Displaying raw signal')
            self.bPB        = np.array([None, None])
            self.aPB        = np.array([None, None])
        elif choice == 0:
            print('Highpass filter from 0.1 Hz')
            self.bPB        = self.b_detrend
            self.aPB        = self.a_detrend
        elif choice == 1:
            print('Bandpass filter between 0.1 and 45 Hz')
            self.bPB        = self.b_wholerange
            self.aPB        = self.a_wholerange
        elif choice == 2:
            print('Bandpass filter between 1 and 30 Hz')
            self.bPB        = self.b_sleep
            self.aPB        = self.a_sleep
        elif choice == 3:
            print('Bandpass filter between 4 and 8 Hz')
            self.bPB        = self.b_theta
            self.aPB        = self.a_theta


    def yrange_selection(self, choice):
        choice              = int(choice)
        if choice == 100:
            print('Vertical range set to -100 uV to +100 uV')
            self.yrange     = (-100, 100)
        elif choice == 200:
            print('Vertical range set to -200 uV to +200 uV')
            self.yrange     = (-200, 200)
        elif choice == 500:
            print('Vertical range set to -500 uV to +500 uV')
            self.yrange     = (-500, 500)
        elif choice == 1000:
            print('Vertical range set to -1000 uV to +1000 uV')
            self.yrange     = (-1000, 1000)
        elif choice == 0:
            print('Vertical range set relative to signal')
            self.yrange     = (-0, 0)


    def disp_envelope(self, choice):
        if choice == True:
            print('Enabled envelope displaying')
            self.envelope = True
        elif choice == False:
            print('Disabled envelope displaying')
            self.envelope = False


    def streamstate(self):
        if not self.streaming:
            self.streambtn.setText('Started')
            self.streaming = True
        elif self.streaming:
            self.streambtn.setText('Stopped')
            self.streaming = False