import serial #Crucial: Install using pip3 install "pyserial", NOT "serial"
import serial.tools.list_ports
import keyboard
import parameters                   as p
from encodings                      import utf_8


class ConfigureBoard:

    def __init__(self):

        # Possible key presses to set board state
        self.states         = ["1", "2", "3", "4", "5"] # List of strings
        self.id             = p.HELMENTID

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
        
        for port in ports:
            print(str(port) + ' - ' + port.hwid)
            if self.id in port.hwid:
                # Bluetooth device query
                self.av_ports["BT"] = port.device
                print('Found Helment connected via Bluetooth')
            elif 'Silicon Labs CP210x USB to UART Bridge' in port.description:
                # USB device query
                self.av_ports["USB"] = port.device
                print('Found Helment connected via USB')

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
        if self.av_ports["BT"] != None:
            self.ser.port   = self.av_ports["BT"]
            str_comtype = 'Board prepared to receive input via Bluetooth'
        elif self.av_ports["USB"] != None:
            self.ser.port   = self.av_ports["USB"]
            str_comtype = 'Board prepared to receive input via USB'
        self.ser.open() # Resets automatically the board
        print(str_comtype)
        

    def query_input(self):
        # =================================================================
        # Listen for valid key presses and send state to board
        # Based on input, call for different methods of this class (ie 
        # reconfigure)
        # INPUT
        #   states          = Valid keyboard presses (list of strings of 
        #                     numbers)
        # OUTPUT
        #   key             = number of keyboard press or default (integer)
        # =================================================================

        key                 = int(-1) # Non-triggering value

        if any(keyboard.is_pressed(key) for key in self.states):
            key = keyboard.read_key()
            key = int(key)

            if key == 0: # "Non-sense" mode (sends defined string)
                print('Asking if board alive')
            elif key == 1: # Standby mode of the board
                print('Putting board to standby. Waiting for new state...')
            elif key == 2: # Start sampling
                if self.av_ports["USB"] == None:
                    raise Exception('USB was chosen but is not available')
                print('Preparing sampling via USB')
            elif key == 3: # Start sampling
                if self.av_ports["BT"] == None:
                    raise Exception('Bluetooth was chosen but is not available')
                print('Preparing sampling via Bluetooth')
            elif key == 4: # Configuration mode
                print('Not implemented: Send configuration')
            elif key == 5: # Reset device
                print('Resetting device')

            self.inform_board(key)

        return key


    def inform_board(self, state):

        state = str(state)

        # Make board aware of key press: Set state of board
        state = bytes(state, 'utf-8')
        self.ser.write(state)
        self.ser.close()
        print('Communicated changes to board: ' + str(state))


    def reconfigure(self, cong_string):
        # Apply firmware config to board
        pass

    def end_session(self):
        # Close down all processes and conections and terminate script
        pass