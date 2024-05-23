import serial
import socket
from threading                          import Thread
from datetime                           import datetime
from pylsl                              import StreamInlet, resolve_stream

class IOManager():

    def __init__(self, parameter):
        #Output
        t0              = str(datetime.now())
        t0              = t0.replace(':', '_')
        if parameter["set_customsession"]:
            file_name   = parameter["sessionName"] + '.txt'
        else:
            file_name   = 'Neuri_' + t0 + '.txt'

        # Prepare data output
        self.output_file= file_name

        with open(self.output_file, 'w', encoding= "utf_8") as file:
            file.write("Session Started\n")
            file.close() # Important for data to get written


    def set_up_serial_entry_point(self, baud_rate, time_out, port):
        # =================================================================
        # Connects to device, preferrably by USB
        # INPUT
        #   baud_rate       = baud rate of the port (scalar)
        #   time_out        = how long a message should be waited for
        #                     default = None (infinite), scalar or None
        #   port            = port to connect to ("COMxy", str)
        # OUTPUT
        #   ser             = Serial connection (object)
        # =================================================================

        # Open communication protocol
        ser            = serial.Serial()
        ser.baudrate   = baud_rate
        ser.timeout    = time_out
        ser.port       = port
        print('Ready to connect to board')
        return ser
    

    def set_up_lsl_entry_point(self):
        streams_eeg = resolve_stream("type", "EEG")
        inlet_eeg = StreamInlet(streams_eeg[0])
        # streams_gyro = resolve_stream("type", "Gyro")
        # inlet_gyro = StreamInlet(streams_gyro[0])
        streams_ppg = resolve_stream("type", "PPG")
        inlet_ppg = StreamInlet(streams_ppg[0])
        return inlet_eeg, inlet_ppg
    

    def set_up_socket_entry_point(self, ip, port):
        receiver_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver_sock.bind((str(ip), int(port)))
        return receiver_sock
    

    def master_write_data(self, eeg_data, time_stamps, saving_interval):
        # =================================================================
        # Input:
        #   eeg_data            2D numpy array [channels x samples] (float)
        #   time_stamps         1D numpy array (float)
        #   saving_interval     Scalar
        # Output:
        #   No output
        # =================================================================
        new_buffer          = eeg_data[:, -saving_interval:]
        new_time_stamps     = time_stamps[-saving_interval:]
            
        save_thread = Thread(target=self.write_data_thread,
            args=(new_buffer, new_time_stamps))
        save_thread.start()


    def calc_sample_rate(self, curr_time, prev_iter_time, sample_rate, time_stamps):

        time_diff           = curr_time - prev_iter_time
        # It took (time_diff) ms to fetch (sample_rate) samples.
        # Calculate actual sampling rate
        actual_sr           = int((sample_rate / (time_diff / 1000)))
        print('%d ms: Writing data (sampling rate = %d Hz)' %
            (time_stamps[-1], actual_sr))


    def write_data_thread(self, eeg_data, time_stamps):
        # =================================================================
        # Input:
        #   eeg_data            2D numpy array [channels x samples] (float)
        #   time_stamps         1D numpy array (float)
        # Output:
        #   No output
        # =================================================================
        # Append the data points to the end of the file
        with open(self.output_file, 'a', encoding= "utf_8") as file:
            buffer_length = time_stamps.shape[0]

            for sample_index in range(buffer_length):
                # Format time stamp
                time_stamp      = time_stamps[sample_index]
                # format eeg data
                eeg_data_points = eeg_data[:,sample_index].tolist()
                eeg_data_points = [str(value) for value in eeg_data_points]
                eeg_data_points = ",".join(eeg_data_points)
                
                # Write line to file
                file.write(f"{time_stamp}, {eeg_data_points} \n")
            file.close() # Important for data to get written


    def build_standard_relay_message(self, s_chans):
        """Build a relay jsonized message string that gets forwarded to any
        third-party application.

        Args:
            s_chans (int): Number of channels (specific for boards)

        Returns relay_array (str):json.format message string with keys for:
            1. timestamps (t)
            2. channels (c)
        """
        relay_array         = {}
        relay_array["t"]    = ''
        for iC in range(s_chans):
            relay_array["".join(["c", str(iC+1)])] = ''
        return relay_array