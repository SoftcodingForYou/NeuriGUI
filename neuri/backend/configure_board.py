import serial #Crucial: Install using pip3 install "pyserial", NOT "serial"
import serial.tools.list_ports
import time

class ConfigureBoard:

    def __init__(self, parameter):
        
        self.pm             = parameter
        self.define_connection()

    
    def define_connection(self):
        # =================================================================
        # Connects to device, preferrably by USB
        # INPUT
        #   baud_rate       = baud rate of the port (scalar)
        #   time_out        = how long a message should be waited for
        #                     default = None (infinite), scalar or None
        #   av_ports        = Dictionnary with values being either None or 
        #                     a strong a the port to connect to
        # OUTPUT
        #   ser             = Serial connection (object)
        # =================================================================

        # Open communication protocol
        self.ser            = serial.Serial()
        self.ser.baudrate   = self.pm.baud_rate
        self.ser.timeout    = self.pm.time_out
        self.ser.port       = self.pm.port
        print('Ready to connect to board')