import serial #Crucial: Install using pip3 install "pyserial", NOT "serial"
import serial.tools.list_ports
import parameters                   as p
import time

class ConfigureBoard:

    def __init__(self):

        self.search_device()
        self.connect_board()


    def search_device(self):
        # =================================================================
        # Scans all ports and fills av_ports with valid serial COM values
        # INPUT
        #   /
        # OUTPUT
        #   av_ports        = Dictionnary of COM values for connection 
        #                     types (object)
        # =================================================================

        self.av_ports       = {'USB': None, 'BT': None}

        # Look for device
        # -----------------------------------------------------------------
        ports = list(serial.tools.list_ports.comports())

        dummyser                = serial.Serial()
        dummyser.baudrate       = p.baud_rate
        dummyser.timeout        = 1
        dummyser.write_timeout  = 1
        for port in ports:
            if 'UART Bridge' in port.description:
                self.av_ports["USB"] = port.device
                print('Found Helment connected via USB')
                continue
            else:
                # Testing for Bluetooth device
                dummyser.port   = port.device
                print('Searching for Neuri via Bluetooth on ' + port.device)
                dummyser.open()
                try:
                    time.sleep(1)
                    dummyser.write(bytes(str(int(3)), 'utf-8')) # Force BT state on board
                    for _ in range(1000):
                        line = str(dummyser.readline())
                        if '{"c1":' in line and '"c2":' in line:
                            self.av_ports["BT"] = port.device
                            print('Found Helment connected via Bluetooth')
                            break
                except:
                    pass
                dummyser.read(dummyser.inWaiting()) # Eliminate message queue at port
                dummyser.close() # Necessary to lierate board

        if all(val == None for val in list(self.av_ports.values())):
            raise Exception('Device could not be found')
        else:
            print(self.av_ports)

    
    def connect_board(self):
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
        self.ser.baudrate   = p.baud_rate
        self.ser.timeout    = p.time_out
        if self.av_ports["BT"] != None: # Priority
            self.ser.port   = self.av_ports["BT"]
            self.des_state  = 3
            str_comtype = 'Board prepared to receive input via Bluetooth'
        elif self.av_ports["USB"] != None: # Fallback solution
            self.ser.port   = self.av_ports["USB"]
            self.des_state  = 2
            str_comtype = 'Board prepared to receive input via USB'
        self.ser.open() # Resets automatically the board
        print(str_comtype)

        self.inform_board(self.des_state)


    def inform_board(self, state):

        if state == 0: # "Non-sense" mode (sends defined string)
            print('Asking if board alive')
        elif state == 1: # Standby mode of the board
            print('Putting board to standby. Waiting for new state...')
        elif state == 2: # Start sampling
            if self.av_ports["USB"] == None:
                raise Exception('USB was chosen but is not available')
            print('Preparing sampling via USB')
        elif state == 3: # Start sampling
            if self.av_ports["BT"] == None:
                raise Exception('Bluetooth was chosen but is not available')
            print('Preparing sampling via Bluetooth')
        elif state == 4: # Configuration mode
            print('Not implemented: Send configuration')
        elif state == 5: # Reset device
            print('Resetting device')

        # Make board aware of key press: Set state of board
        state = bytes(str(state), 'utf-8')
        self.ser.write(state)
        self.ser.read(self.ser.inWaiting()) # Eliminate message queue at port
        self.ser.close()
        print('Communicated changes to board')


    def reconfigure(self, cong_string):
        # Apply firmware config to board
        pass

    def end_session(self):
        # Close down all processes and conections and terminate script
        pass