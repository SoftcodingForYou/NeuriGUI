import serial #Crucial: Install using pip3 install "pyserial", NOT "serial"
import serial.tools.list_ports
import time
import json
import numpy as np
from bluetooth import discover_devices

class CountMeLikeOneYourFrenchGirls:

    def __init__(self):

        self.COM            = '' # COM port here (string such as "COM3")
        self.BAUDRATE       = 115200 # scalar
        self.TIMEOUT        = None # Blocking = codes waiting for sample

        self.connect_board()
        self.sampling()


    def connect_board(self):

        ports       = list(serial.tools.list_ports.comports())
        # bt_devices  = discover_devices(lookup_names = True)
        
        for port in ports:
            print(str(port) + ' - ' + port.hwid)
            if 'Silicon Labs CP210x USB to UART Bridge' in port.description:
                continue
                self.COM        = port.device
                self.command    = b'2'
                self.contype    = 'USB'
                print('Found Helment connected via USB')
            elif '7&74D8485&0&7C9EBDABB922_C00000000' in port.hwid:
                self.COM        = port.device
                self.command    = b'3'
                self.contype    = 'BT'
                print('Found Helment connected via Bluetooth')

        if self.COM == '':
            raise Exception('Device not found')

        # Open communication protocol
        self.ser            = serial.Serial()
        self.ser.baudrate   = self.BAUDRATE
        self.ser.timeout    = self.TIMEOUT
        self.ser.port       = self.COM
        self.ser.open()
        print('Connection established via ' + self.contype)

        time.sleep(5)
        self.ser.write(self.command)


    def sampling(self):

        i_sample            = 0
        t_now               = round(time.perf_counter() * 1000, 4) # ms

        board_booting = True
        print('Board is booting up ...')
        while board_booting:
            raw_message = str(self.ser.readline())
            print(raw_message)
            if '{' in raw_message and '}' in raw_message:
                print('Fully started')
                board_booting = False
            
        while True:
            
            t_iteration     = round(time.perf_counter() * 1000, 4) # ms
            raw_message     = str(self.ser.readline())
            # print(raw_message)

            idx_start           = raw_message.find("{")
            idx_stop            = raw_message.find("}")
            raw_message         = raw_message[idx_start:idx_stop+1]
            eeg_data_line       = json.loads(raw_message)

            i_sample        = i_sample + 1

            if '{' not in raw_message or '}' not in raw_message:
                continue

            idx_start           = raw_message.find("{")
            idx_stop            = raw_message.find("}")
            raw_message         = raw_message[idx_start:idx_stop+1]
            
            # Process samples
            eeg_data_line       = json.loads(raw_message)
            # print(eeg_data_line["c1"])
            # print(np.diff(eeg_data_line["c1"]))

            if t_iteration >= t_now + 1000:
                t_diff      = (t_iteration - t_now) / 1000
                sample_freq = round(i_sample / t_diff, 1)
                t_now       = t_iteration
                print('Sample frequency is (Hz): ' + str(sample_freq))
                i_sample    = 0


if __name__ == '__main__': # Necessary line for "multiprocessing" to work

    CountTheFrenchs = CountMeLikeOneYourFrenchGirls()