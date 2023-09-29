#Prepare userland =========================================================
from backend.Helment_signal_processing      import Processing
from backend.Helment_configure_board        import ConfigureBoard
from backend.Helment_signal_sampling        import Sampling
from backend.Helment_parameter_validation   import ParamVal
from frontend.Helment_widgets               import GUIWidgets
from frontend.Helment_user_experience       import Aux
from frontend.Helment_parameters            import Parameters
from multiprocessing                        import Process, Pipe
from PyQt5                                  import QtCore, QtGui, QtWidgets
import sys  # We need sys so that we can pass argv to QApplication
import os


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):

        QtWidgets.QMainWindow.__init__(self)

        # Set parameters
        # -----------------------------------------------------------------
        pm                  = Parameters()
        ParamVal(pm)        # Sanity checks

        # Initialize filter coefficient arrays
        # -----------------------------------------------------------------
        proc                = Processing(pm)

        # Splash screen
        # -----------------------------------------------------------------
        # auxgui              = Aux()
        # splash, pb          = auxgui.disp_splash()
        # auxgui.report_progress(splash, pb, 5)

        guiwidgets          = GUIWidgets(self, proc, pm)

        # Inherit processing functions that will be used during plot update
        guiwidgets.prepare_buffer   = proc.prepare_buffer
        guiwidgets.extract_envelope = proc.extract_envelope

        # auxgui.report_progress(splash, pb, 5)

        # Load methods and build communication with EEG board
        # -----------------------------------------------------------------
        # auxgui.report_progress(splash, pb, 5)
        confboard           = ConfigureBoard(pm)  # Board communication
        # auxgui.report_progress(splash, pb, 20)
        sampl               = Sampling(pm)        # Signal handling
        # auxgui.report_progress(splash, pb, 5)

        # Build GUI
        # -----------------------------------------------------------------
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle('Helment EEG GUI (raw data available at {}:{})'.format(sampl.udp_ip, sampl.udp_port))
        
        # This following line causes and X11 error on GNU/Linux (tried with
        # various distributions)
        # self.setWindowIcon(QtGui.QIcon(pm.img_helment))
        
        self.central_widget = QtWidgets.QWidget() # A QWidget to work as Central Widget

        # Without specifying, this just makes the GUI separable vertically
        # and horizontally 
        vertlayout          = QtWidgets.QVBoxLayout() # Vertical Layout
        controlpanel        = QtWidgets.QHBoxLayout() # Horizontal Layout

        # Load frontend elements
        widget_vrange       = guiwidgets.fg_vert_range()
        widget_notch        = guiwidgets.fg_notch_filter()
        widget_bandpass     = guiwidgets.fg_bandpass_filter()
        widget_envelope     = guiwidgets.fg_envelope()
        widget_sbtn         = guiwidgets.fg_stream_button()
        widget_darkmode     = guiwidgets.fg_theme_button()
        widget_signal       = guiwidgets.fg_signal_stream() # widget_signal also contains channel signals

        guiwidgets.initiate_theme() # Needs to be called after widget 
                                    # elements initiation since hard-coded
        # auxgui.report_progress(splash, pb, 15)

        vertlayout.addLayout(controlpanel)
        controlpanel.addWidget(widget_vrange)
        controlpanel.addWidget(widget_notch)
        controlpanel.addWidget(widget_bandpass)
        controlpanel.addWidget(widget_envelope)
        controlpanel.addWidget(widget_sbtn)
        controlpanel.addWidget(widget_darkmode)
        vertlayout.addWidget(widget_signal)
        # auxgui.report_progress(splash, pb, 5)

        # Generate variable exchange pipe
        # -----------------------------------------------------------------
        self.recv_conn, self.send_conn = Pipe(duplex = False)

        # Generate separate processes to not slow down sampling by any
        # other executions
        # -----------------------------------------------------------------
        self.sampling    = Process(target=sampl.fetch_sample,
            args=(self.send_conn, confboard.ser, 
            pm.port, pm.firmfeedback))
        
        if pm.firmfeedback == 2 or pm.firmfeedback == 3:
            self.sampling.start()
        # auxgui.report_progress(splash, pb, 10)
        
        ## Finalize
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(vertlayout) # Draw elements in main widget
        # auxgui.report_progress(splash, pb, 10)

        self.timer          = QtCore.QTimer()
        self.timer.setInterval(0)
        self.timer.timeout.connect(lambda: guiwidgets.update_signal_plot(self.recv_conn))
        self.timer.singleShot = False
        
        # Splash screen needs to be closed before timer start
        # auxgui.report_progress(splash, pb, 19)
        # splash.destroy()
        self.timer.start()
        

    def on_closing(self):
        self.timer.stop()
        self.sampling.terminate()
        self.recv_conn.close()
        self.send_conn.close()


if __name__ == '__main__': # Necessary line for "multiprocessing" to work
    # pyqt = os.path.dirname(PyQt5.__file__)
    # os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt, "Qt/plugins")

    app                     = QtWidgets.QApplication(sys.argv)
    maingui                 = MainWindow()  # Contains all necessary bits
    maingui.show()
    app.exec_()
    maingui.on_closing()
    sys.exit()  # Proper way would be "sys.exit(app.exec_())" but it does  
                # not return the main console
    