#Prepare userland =========================================================
from PyQt5                                  import QtCore, QtWidgets, QtGui
from pyqtgraph                              import PlotWidget
import pyqtgraph                            as pg
from numpy import max, abs, array, zeros, reshape
import os


class GUIWidgets():

    def __init__(self, mainwindow, processing, parameter):

        super(GUIWidgets, self).__init__() # Init Processing class first

        # Load parameters
        # -----------------------------------------------------------------
        self.displ_chans    = [i for i in range(parameter.max_chans) if parameter.selected_chans[i]]
        self.numchans       = len(self.displ_chans)
        self.count          = 0
        self.yrange         = parameter.yrange
        self.notch          = parameter.notch
        self.bpass          = parameter.bpass
        self.denv           = parameter.dispenv
        self.yrange         = parameter.yrange

        # Defaults
        self.streaming      = True
        self.envelope       = False
        self.bSB            = processing.b_notch
        self.aSB            = processing.a_notch
        self.bPB            = processing.b_wholerange
        self.aPB            = processing.a_wholerange
        self.lighttheme     = QtGui.QGuiApplication.palette()
        self.darktheme      = self.define_darktheme()
        self.darkmode       = parameter.darkmode
        self.mainwindow     = mainwindow

        self.proc           = processing


    def initiate_theme(self):
        if self.darkmode:
            self.apply_dark_theme()
        elif not self.darkmode:
            self.apply_light_theme()
        

    def fg_vert_range(self):
        # -----------------------------------------------------------------
        # Vert. range (uV)
        # rbt1 (Auto) rdbt2 (100) rdbt3 (200) rdbt4 (500) rdbt5 (1000)
        # -----------------------------------------------------------------
        self.vert_range     = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()
        horilayout          = QtWidgets.QHBoxLayout()
        title               = QtWidgets.QLabel('Vertical range (uV)')
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
        self.vert_range.setLayout(vertlayout)

        return self.vert_range
    

    def fg_notch_filter(self):
        # -----------------------------------------------------------------
        # Notch filter
        # rbt1 (50 Hz) rdbt2 (60 Hz) rdbt3 (Off)
        # -----------------------------------------------------------------
        self.notch_filter   = QtWidgets.QWidget()
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
        self.notch_filter.setLayout(vertlayout)

        return self.notch_filter
    

    def fg_bandpass_filter(self):
        # -----------------------------------------------------------------
        # Bandpass (Hz)
        # rbt1 (0.5 - 45) rdbt2 (1 - 30) rdbt3 (4 - 8)
        # -----------------------------------------------------------------
        self.bandpass_filter= QtWidgets.QWidget()
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
        self.bandpass_filter.setLayout(vertlayout)

        return self.bandpass_filter
    

    def fg_envelope(self):
        # -----------------------------------------------------------------
        # Display envelope
        # rbt1 (Off) rdbt2 (On)
        # -----------------------------------------------------------------
        self.envel          = QtWidgets.QWidget()
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
        self.envel.setLayout(vertlayout)

        return self.envel
    

    def fg_stream_button(self):
        # -----------------------------------------------------------------
        # Data stream
        # Dynamic button (Start/Stop (default))
        # -----------------------------------------------------------------
        self.stream         = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()
        title               = QtWidgets.QLabel('Data stream')
        self.streambtn      = QtWidgets.QPushButton(text="Started")

        self.streambtn.clicked.connect(self.streamstate)

        vertlayout.addWidget(title)
        vertlayout.addWidget(self.streambtn)
        self.stream.setLayout(vertlayout)
        
        return self.stream
    

    def fg_theme_button(self):
        self.theme          = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()
        title               = QtWidgets.QLabel('Current theme')

        if self.darkmode:
            self.themebtn   = QtWidgets.QPushButton(text="Dark")
        elif not self.darkmode:
            self.themebtn   = QtWidgets.QPushButton(text="Light")

        self.themebtn.clicked.connect(self.themestate)

        vertlayout.addWidget(title)
        vertlayout.addWidget(self.themebtn)
        self.theme.setLayout(vertlayout)
        
        return self.theme
    

    def fg_signal_stream(self, num_samples, s_down, displ_chans, sampling_rate):
        self.signal         = QtWidgets.QWidget()
        vertlayout          = QtWidgets.QVBoxLayout()

        self.x              = list(range(-num_samples, 0, s_down))
        self.x              = [x/sampling_rate for x in self.x]
        self.xplot          = array(self.x) # Non-sense action to avoid pointers (force creation of other id())
        self.y              = zeros((len(displ_chans), int(num_samples/s_down)), dtype=float)
        self.data_line      = {}
        self.signalgraph    = {}
        self.penstyle       = {}

        for iChan in range(len(displ_chans)):

            self.signalgraph[iChan] = PlotWidget()

            # Aesthetics
            self.signalgraph[iChan].setBackground('w')
            self.signalgraph[iChan].setLabel('left', 'A (uV)')
            if iChan == len(displ_chans) -1:
                self.signalgraph[iChan].setLabel('bottom', '')
            else:
                self.signalgraph[iChan].setLabel('bottom', '')
                # self.signalgraph[iChan].getAxis('bottom').setTicks([])
            self.signalgraph[iChan].showGrid(x=False, y=True)
            self.penstyle[iChan] = pg.mkPen(color=(49,130,189), width=2)
            
            # Decorate plot
            legend = self.signalgraph[iChan].addLegend(offset=(5, 0))
            self.signalgraph[iChan].setAntialiasing(False)  # Huge performance gain and 
                                                # necessary to keep up with 
                                                # the sampling rate
            self.signalgraph[iChan].setYRange(self.yrange[0], self.yrange[1])
            self.signalgraph[iChan].setRange(
                yRange=(self.yrange[0], self.yrange[1]), 
                padding=0, disableAutoRange=True)
            self.signalgraph[iChan].setMinimumSize(200, 50)
            
            # Set signal lines
            self.data_line[iChan] = self.signalgraph[iChan].plot(
                self.xplot, self.y[iChan,:],
                name='Ch. {}'.format(str(displ_chans[iChan]+1)),
                pen=self.penstyle[iChan])

            # Disable interactivity
            self.signalgraph[iChan].setMouseEnabled(x=False, y=False)
            self.signalgraph[iChan].hideButtons()
            self.signalgraph[iChan].getPlotItem().setMenuEnabled(False)
            legend.mouseDragEvent = lambda *args, **kwargs: None
            legend.hoverEvent = lambda *args, **kwargs: None

            # Fix sizes in order to avoid filling of white spaces
            # self.signalgraph[iChan].getViewBox().size()
            # self.signalgraph[iChan].getAxis('bottom').setWidth(
            #     self.signalgraph[iChan].getAxis('bottom').size().width())

            vertlayout.addWidget(self.signalgraph[iChan])

        self.signal.setLayout(vertlayout)

        return self.signal


    def update_signal_plot(self, recv_conn, s_down, left_edge,
                           sampling_rate, idx_retain, displ_chans):

        # Update plots for every channel
        # -----------------------------------------------------------------
        buffer, t_now   = recv_conn.recv()

        self.count = self.count + 1
        if self.count < s_down:
            return

        # Filter buffer signal and send filtered data to plotting funcs
        # -------------------------------------------------------------
        processed_buffer    = self.prepare_buffer(buffer, 
            self.bSB, self.aSB, self.bPB, self.aPB)
        processed_buffer    = processed_buffer[:, left_edge:]

        if self.envelope == True:
            processed_buffer = self.extract_envelope(processed_buffer)

        self.x          = self.x[1:]  # Remove the first y element
        self.x.append(self.x[-1]+self.count/sampling_rate) # t_now/1000

        if self.streaming == True:
            self.xplot      = self.x

        
        # Downsample buffer
        down_buffer = processed_buffer[:, idx_retain]

        # Set vertical range
        v_buffer    = reshape(down_buffer, down_buffer.size)
        if self.yrange[1] == 0:
            vscale = [
                -max([abs(min(v_buffer)), abs(max(v_buffer))]),
                max([abs(min(v_buffer)), abs(max(v_buffer))])]
        else:
            vscale = self.yrange
        

        # Update plots for every channel
        # -------------------------------------------------------------
        for iChan in range(len(displ_chans)):

            if self.streaming == True:
                self.y[iChan,:] = down_buffer[displ_chans[iChan], :]
            
            self.data_line[iChan].setData(self.x, self.y[iChan])  # Update the data

            if self.envelope == True:
                self.signalgraph[iChan].setYRange(0, vscale[1], padding=0)
            else:
                self.signalgraph[iChan].setYRange(vscale[0], vscale[1], padding=0)

        self.count          = 0

    
    def filt_noise(self, choice):
        choice = int(choice)
        if choice == 50:
            print('Enabled 50 Hz stopband filter')
            self.bSB    = self.proc.b_notch
            self.aSB    = self.proc.a_notch
        elif choice == 60:
            print('Enabled 60 Hz stopband filter')
            self.bSB    = self.proc.b_notch60
            self.aSB    = self.proc.a_notch60
        elif choice == 0:
            print('Notch filter disabled')
            self.bSB    = array([None, None]) # Avoiding bool not iterable
            self.aSB    = array([None, None])


    def filt_bandpass(self, choice):
        choice = int(choice)
        if choice == -1:
            print('Displaying raw signal')
            self.bPB        = array([None, None])
            self.aPB        = array([None, None])
        elif choice == 0:
            print('Highpass filter from 0.1 Hz')
            self.bPB        = self.proc.b_detrend
            self.aPB        = self.proc.a_detrend
        elif choice == 1:
            print('Bandpass filter between 0.1 and 45 Hz')
            self.bPB        = self.proc.b_wholerange
            self.aPB        = self.proc.a_wholerange
        elif choice == 2:
            print('Bandpass filter between 1 and 30 Hz')
            self.bPB        = self.proc.b_sleep
            self.aPB        = self.proc.a_sleep
        elif choice == 3:
            print('Bandpass filter between 4 and 8 Hz')
            self.bPB        = self.proc.b_theta
            self.aPB        = self.proc.a_theta


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


    def themestate(self):

        if self.darkmode:
            self.themebtn.setText('Light')
            self.apply_light_theme()
            self.darkmode = False
            self.save_parameters()
            print('Enabled light theme')
        elif not self.darkmode:
            self.themebtn.setText('Dark')
            self.apply_dark_theme()
            self.darkmode = True
            self.save_parameters()
            print('Enabled dark theme')


    def save_parameters(self):

        end_line        = "\n"
        conf_file       = './settings.cfg'

        if not os.path.exists(conf_file): # File generation

            with open(conf_file, 'w') as f:
                f.write("".join(["Darkmode=", str(self.darkmode), end_line]))

        else:

            with open(conf_file, 'r') as f:
            
                settings                        = f.readlines()
                
                for i, setting in enumerate(settings): # Update values
                    if 'Darkmode' in setting:
                        settings[i]             = "".join(["Darkmode=", str(self.darkmode), end_line])

                new_settings = []
                if len([s for s in settings if "Darkmode" in s]) == 0:
                    new_settings.append("".join(["Darkmode=", str(self.darkmode), end_line]))

            with open(conf_file, 'w') as f:
                f.write("".join(settings + new_settings))


    def define_darktheme(self):
        darktheme = QtGui.QPalette()
        darktheme.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
        darktheme.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        darktheme.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
        darktheme.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        darktheme.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.black)
        darktheme.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        darktheme.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        darktheme.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
        darktheme.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        darktheme.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        darktheme.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        darktheme.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        darktheme.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)

        return darktheme


    def apply_light_theme(self):
        self.signal.setPalette(self.lighttheme)
        self.theme.setPalette(self.lighttheme)
        self.stream.setPalette(self.lighttheme)
        self.bandpass_filter.setPalette(self.lighttheme)
        self.notch_filter.setPalette(self.lighttheme)
        self.envel.setPalette(self.lighttheme)
        self.vert_range.setPalette(self.lighttheme)
        self.streambtn.setPalette(self.lighttheme)
        self.themebtn.setPalette(self.lighttheme)
        self.streambtn.setStyleSheet(
            'QPushButton {background-color: rgb(222,235,247); border-radius: 10px;padding: 6px;color: #08519c;}')
        self.themebtn.setStyleSheet(
            'QPushButton {background-color: rgb(222,235,247); border-radius: 10px;padding: 6px;color: #08519c;}')
        self.mainwindow.setPalette(self.lighttheme)

        for iChan in range(self.numchans):
            self.signalgraph[iChan].setBackground((247,247,247))
            self.penstyle[iChan] = pg.mkPen(color=(49,130,189), width=2)


    def apply_dark_theme(self):        
        self.signal.setPalette(self.darktheme)
        self.theme.setPalette(self.darktheme)
        self.stream.setPalette(self.darktheme)
        self.bandpass_filter.setPalette(self.darktheme)
        self.notch_filter.setPalette(self.darktheme)
        self.envel.setPalette(self.darktheme)
        self.vert_range.setPalette(self.darktheme)
        self.streambtn.setPalette(self.darktheme)
        self.themebtn.setPalette(self.darktheme)
        self.streambtn.setStyleSheet(
            'QPushButton {background-color: rgb(49,130,189); border-radius: 10px;padding: 6px; color: #eff3ff;}')
        self.themebtn.setStyleSheet(
            'QPushButton {background-color: rgb(49,130,189); border-radius: 10px;padding: 6px; color: #eff3ff;}')
        self.mainwindow.setPalette(self.darktheme)

        for iChan in range(self.numchans):
            self.signalgraph[iChan].setBackground((37,37,37))
            self.penstyle[iChan] = pg.mkPen(color=(222,235,247), width=2)