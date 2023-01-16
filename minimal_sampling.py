import serial #Crucial: Install using pip3 install "pyserial", NOT "serial"
import serial.tools.list_ports
import time

class CountMeLikeOneYourFrenchGirls:

    def __init__(self):

        self.COM            = '' # COM port here (string such as "COM3")
        self.BAUDRATE       = 115200 # scalar
        self.TIMEOUT        = None # Blocking = codes waiting for sample

        self.connect_board()
        self.sampling()


    def connect_board(self):

        myports             = [tuple(ports) for ports in 
            list(serial.tools.list_ports.comports())]
        
        for iPort in range(len(myports)):
            print(list(myports[iPort]))
            if 'Silicon Labs CP210x USB to UART Bridge' in list(myports[iPort])[1]:
                continue
                self.COM        = list(myports[iPort])[0]
                self.command    = b'2'
                self.contype    = 'USB'
                print('Found Helment connected via USB')
            elif '7&2F45FB97&0&24D7EBA43B56_C00000000' in list(myports[iPort])[2]:
                self.COM        = list(myports[iPort])[0]
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

        time.sleep(10)
        self.ser.write(self.command)


    def sampling(self):

        i_sample            = 0
        t_now               = round(time.perf_counter() * 1000, 4) # ms
            
        while True:
            
            t_iteration     = round(time.perf_counter() * 1000, 4) # ms
            raw_message     = str(self.ser.readline())
            # print(raw_message)
            i_sample        = i_sample + 1

            if t_iteration >= t_now + 1000:
                t_diff      = (t_iteration - t_now) / 1000
                sample_freq = round(i_sample / t_diff, 1)
                t_now       = t_iteration
                print('Sample frequency is (Hz): ' + str(sample_freq))
                i_sample    = 0


if __name__ == '__main__': # Necessary line for "multiprocessing" to work

    CountTheFrenchs = CountMeLikeOneYourFrenchGirls()