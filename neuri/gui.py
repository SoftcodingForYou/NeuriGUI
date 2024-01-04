#Prepare userland =========================================================

# Necessary step for relative imports when the GUI is run directly in an 
# IDE instead of as module
if ( __package__ == "" or __package__ == None ):
    from backend.signal_processing              import Processing
    from backend.configure_board                import ConfigureBoard
    from backend.signal_sampling                import Sampling
    from backend.parameter_validation           import ParamVal
    from frontend.widgets                       import GUIWidgets
    from frontend.user_experience               import Aux
    from frontend.parameters                    import Parameters
else:
    from .backend.signal_processing             import Processing
    from .backend.configure_board               import ConfigureBoard
    from .backend.signal_sampling               import Sampling
    from .backend.parameter_validation          import ParamVal
    from .frontend.widgets                      import GUIWidgets
    from .frontend.user_experience              import Aux
    from .frontend.parameters                   import Parameters

from multiprocessing                            import Process, Array, Value
from PyQt5                                      import QtCore, QtWidgets
from numpy                                      import zeros
from time                                       import sleep
import sys  # We need sys so that we can pass argv to QApplication


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

        # Load methods and build communication with EEG board
        # -----------------------------------------------------------------
        # auxgui.report_progress(splash, pb, 5)
        confboard           = ConfigureBoard(pm)  # Board communication
        # auxgui.report_progress(splash, pb, 20)
        sampl               = Sampling(pm)        # Signal handling
        # auxgui.report_progress(splash, pb, 5)

        # Generate variable exchange variables (shared memory allocations)
        # -----------------------------------------------------------------
        shared_buffer                   = Array(
            'd', zeros(( 
                (pm.buffer_length + pm.buffer_add) * pm.sample_rate * pm.max_chans
                )), lock = True)
        shared_timestamp                = Value('i', 0)
        self.gui_running                = Value('i', 1)

        # Generate separate processes to not slow down sampling by any
        # other executions
        # -----------------------------------------------------------------

        # Here, we can not just parse "pm" as it contains non-pickable tk 
        # objects which will break at self.sampling.start(). We create a 
        # new object with the necessary variables only
        strpm = StreamingParameter(
            pm.firmfeedback, pm.max_chans, pm.buffer_add, pm.buffer_length,
            pm.sample_rate, pm.PGA, pm.saving_interval, pm.udp_ip,
            pm.udp_port)
        self.board_port = confboard.ser
        self.sampling    = Process(target=sampl.fetch_sample,
            args=(confboard.ser, pm.send_sock, strpm,
                  shared_buffer, shared_timestamp, self.gui_running))

        # Build GUI
        # -----------------------------------------------------------------
        super(MainWindow, self).__init__(*args, **kwargs)
        
        # This following line causes and X11 error on GNU/Linux (tried with
        # various distributions)
        # self.setWindowIcon(QtGui.QIcon(pm.img_helment))
        
        guiwidgets          = GUIWidgets(self, proc, pm)
        # Inherit processing functions that will be used during plot update
        guiwidgets.prepare_buffer   = proc.prepare_buffer
        guiwidgets.extract_envelope = proc.extract_envelope
        
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
        widget_fps          = guiwidgets.display_fps()
        widget_signal       = guiwidgets.fg_signal_stream(
            int(pm.sample_rate * pm.buffer_length), pm.s_down,
            [i for i in range(pm.max_chans) if pm.selected_chans[i]],
            pm.sample_rate)
        widget_headless     = guiwidgets.fg_static_info(pm.udp_ip, pm.udp_port)

        guiwidgets.initiate_theme() # Needs to be called after widget 
                                    # elements initiation since hard-coded
        # auxgui.report_progress(splash, pb, 15)

        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(vertlayout) # Draw elements in main widget
        # auxgui.report_progress(splash, pb, 10)

        self.timer              = QtCore.QTimer()
        self.timer.setInterval(20)  # This can be set to 0 as well for
                                    # fastest plotting calls possible but
                                    # the GUI currently freezes in those
                                    # conditions and I have not figured out
                                    # how to use QThreads accordingly
                                    # (window does not get updated if 
                                    # update plot functions are inside
                                    # QThread)
        self.timer.singleShot   = False

        if pm.run_headless:

            self.setWindowTitle("Headless sampling")

            # Add GUI elements
            vertlayout.addWidget(widget_headless)
            self.setCentralWidget(self.central_widget)
            self.central_widget.setLayout(vertlayout) # Draw elements in main widget

            # Prepare buffer-emptying function
            self.timer.timeout.connect(lambda: sampl.headless_sampling(shared_buffer, shared_timestamp))

        else:
            
            self.setWindowTitle('Helment EEG GUI (raw data available at {}:{})'.format(pm.udp_ip, pm.udp_port))

            # Add GUI elements
            vertlayout.addLayout(controlpanel)
            controlpanel.addWidget(widget_vrange)
            controlpanel.addWidget(widget_notch)
            controlpanel.addWidget(widget_bandpass)
            controlpanel.addWidget(widget_envelope)
            controlpanel.addWidget(widget_sbtn)
            controlpanel.addWidget(widget_darkmode)
            controlpanel.addWidget(widget_fps)
            vertlayout.addWidget(widget_signal)
            
            # Prepare data visualization
            self.timer.timeout.connect(lambda: guiwidgets.update_signal_plot(
                pm.s_down, int(pm.sample_rate * pm.buffer_add),
                pm.sample_rate,
                range(0, int(pm.sample_rate * pm.buffer_length), pm.s_down), pm.max_chans,
                [i for i in range(pm.max_chans) if pm.selected_chans[i]], shared_buffer, shared_timestamp))

        # Splash screen needs to be closed before timer start
        # auxgui.report_progress(splash, pb, 19)
        # splash.destroy()

        # Start sampling processes
        # -----------------------------------------------------------------
        if pm.firmfeedback == 2 or pm.firmfeedback == 3:
            self.sampling.start()
        self.timer.start()
        

    def on_closing(self):
        self.gui_running.value = 0
        sleep(2) # A second longer than the sampling thread
        self.timer.stop()
        self.sampling.terminate()


class StreamingParameter(object):
    firmfeedback    = 0
    max_chans       = 0
    buffer_add      = 0
    buffer_length   = 0
    sample_rate     = 0
    PGA             = 0
    saving_interval = 0
    udp_ip          = ""
    udp_port        = 0

    # The class "constructor" - It's actually an initializer 
    def __init__(self, firmfeedback, max_chans, buffer_add, buffer_length,
                 sample_rate, PGA, saving_interval, udp_ip, udp_port):
        self.firmfeedback   = firmfeedback
        self.max_chans      = max_chans
        self.buffer_add     = buffer_add
        self.buffer_length  = buffer_length
        self.sample_rate    = sample_rate
        self.PGA            = PGA
        self.saving_interval= saving_interval
        self.udp_ip         = udp_ip
        self.udp_port       = udp_port


class Run():

    def __init__(self):

        app                     = QtWidgets.QApplication(sys.argv)
        maingui                 = MainWindow()  # Contains all necessary bits
        maingui.show()
        app.exec_()
        maingui.on_closing()
        if ( __package__ == "" or __package__ == None ):
            sys.exit()
        else:
            # sys.exit(app.exec_())
            app.quit()
    

if __name__ == '__main__': # If run from IDEs instead of as module
    Run()