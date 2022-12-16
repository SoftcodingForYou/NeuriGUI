#Prepare userland =========================================================
import parameters                           as p
from backend.Helment_signal_processing      import Processing
from backend.Helment_configure_board        import ConfigureBoard
from backend.Helment_signal_sampling        import Sampling
from backend.Helment_parameter_validation   import ParamVal
from multiprocessing                        import Process, Pipe
from PyQt5                                  import QtWidgets, QtCore
from pyqtgraph                              import PlotWidget, plot
import pyqtgraph                            as pg
import sys  # We need sys so that we can pass argv to QApplication
import os


class MainWindow(QtWidgets.QMainWindow, Processing):

    def __init__(self, *args, **kwargs):

        # Load parameters
        # -----------------------------------------------------------------
        self.numchans       = p.buffer_channels
        self.numsamples     = int(p.sample_rate * p.buffer_length)
        self.left_edge      = int(p.sample_rate * p.buffer_add)
        self.samplerate     = p.sample_rate
        self.count          = 0
        self.s_down         = p.s_down
        self.idx_retain     = range(0, int(p.sample_rate * p.buffer_length), p.s_down)

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
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = PlotWidget()
        self.setCentralWidget(self.graphWidget)

        self.x = list(range(-self.numsamples, 0, self.s_down))
        self.x = [x/self.samplerate for x in self.x]
        self.y = [0 for _ in range(0, self.numsamples, self.s_down)]

        self.graphWidget.setBackground('w')
        self.graphWidget.setYRange(p.yrange[0], p.yrange[1])
        self.graphWidget.setRange(yRange=(p.yrange[0], p.yrange[1]), disableAutoRange=True)
        self.graphWidget.addLegend()

        # Decorate plot
        # -----------------------------------------------------------------
        pen1 = pg.mkPen(color=(255, 0, 0), width=1)
        pen2 = pg.mkPen(color=(0, 0, 255), width=1)
        self.data_line = {}
        self.data_line[0] =  self.graphWidget.plot(self.x, self.y, name='Channel 1', pen=pen1)
        self.data_line[1] =  self.graphWidget.plot(self.x, self.y, name='Channel 2', pen=pen2)
        self.graphWidget.setLabel('left', 'Amplitude (uV)')
        self.graphWidget.setLabel('bottom', 'Time (s)')
        
        self.graphWidget.setAntialiasing(False)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(0)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.singleShot = False
        self.timer.start()
        print('Starting... Window may seem non-responsive for some seconds')


    def update_plot_data(self):

        # Update plots for every channel
        # -----------------------------------------------------------------
        buffer, t_now   = self.recv_conn.recv()

        self.count = self.count + 1
        if self.count < self.s_down:
            return

        # Filter buffer signal and send filtered data to plotting funcs
        # -------------------------------------------------------------
        processed_buffer    = self.prepare_buffer(buffer)
        processed_buffer    = processed_buffer[:, self.left_edge:]

        self.x              = self.x[1:]  # Remove the first y element
        self.x.append(self.x[-1]+self.count/self.samplerate) # t_now/1000

        for iChan in range(self.numchans):
            self.y = processed_buffer[iChan, self.idx_retain]
            self.data_line[iChan].setData(self.x, self.y)  # Update the data
        self.count          = 0


if __name__ == '__main__': # Necessary line for "multiprocessing" to work
    
    app                     = QtWidgets.QApplication(sys.argv)
    sigplots                = MainWindow()  # Contains all necessary bits
    sigplots.show()
    app.exec_()
    sigplots.sampling.terminate()
    sys.exit(app.exec_())

