import json
import keyboard
import time
import parameters                       as p
import numpy                            as np
from backend.Helment_signal_processing  import Processing
from threading                          import Thread
from datetime                           import datetime


class Sampling(Processing):

    def __init__(self):

        #Output
        t0              = str(datetime.now())
        t0              = t0.replace(':', '_')
        file_name       = 'Helment ' + t0 + '.txt'

        self.py_start   = round(time.perf_counter() * 1000, 4)
        self.pga        = p.PGA

        # Prepare data output
        self.output_file= file_name
        self.buffer     = np.zeros((p.buffer_channels, 
            p.buffer_length * p.sample_rate))
        self.time_stamps= np.zeros(p.buffer_length * p.sample_rate)

        with open(self.output_file, 'w', encoding= "utf_8") as file:
            file.write("Session Started\n")
            file.close() # Important for data to get written

        # Sample fetching parameters
        self.sample_count       = p.sample_count # From parameters
        self.saving_interval    = p.saving_interval * p.sample_rate # From parameters
        self.time_reset         = self.py_start
        self.sample_rate        = p.sample_rate

        self.numchans   = p.buffer_channels

        self.prepare_filters()


    def bin_to_voltage(self, bin):
        # =================================================================
        # Convert binary into volts
        # =================================================================
        #bin = int(bin) # requieres int

        if bin == 0:
            return 0
        if bin > 0 and bin <= 8388607:
            sign_bit = bin
        elif bin > 8388607 and bin <= 2*8388607:
            sign_bit = -2*8388607 + bin - 1
        
        voltage = (4.5*sign_bit)/(self.pga*8388607.0)
        voltage = voltage * 1000000 # Convert to microvolts
        return voltage


    def fetch_sample(self, pipe_conn, ser, cons, desired_con):

        if desired_con == 2: # Bluetooth
            ser.port        = cons["USB"]
            s_per_buffer    = 1
            print('USB')
        elif desired_con == 3: # USB
            ser.port        = cons["BT"]
            s_per_buffer    = 1 #10
            print('BT')

        # Open communication ----------------------------------------------
        if ser.port == None:
            raise Exception('Verify that desired connection type (USB or Bluetooth) are indeed available')
        else:
            ser.open()

        ser.write(bytes(str(desired_con), 'utf-8'))

        board_booting = True
        print('Board is booting up ...')
        while board_booting and not keyboard.is_pressed('c'):
            raw_message = str(ser.readline())
            if '{' in raw_message and '}' in raw_message:
                print('Fully started')
                board_booting = False
            
        while not keyboard.is_pressed('c'): # Alternatively "while True:"
        
            raw_message = str(ser.readline())

            idx_start           = raw_message.find("{")
            idx_stop            = raw_message.find("}")
            raw_message         = raw_message[idx_start:idx_stop+1]
            
            # Handle JSON samples and add to signal buffer ----------------
            eeg_data_line       = json.loads(raw_message)

            # Each channel carries self.s_per_buffer amounts of samples
            for iS in range(s_per_buffer):

                self.sample_count   = self.sample_count + 1
                if s_per_buffer > 1:
                    buffer_line = [eeg_data_line['c1'][iS],eeg_data_line['c2'][iS]]
                else:
                    buffer_line = [eeg_data_line['c1'],eeg_data_line['c2']]
                sample          = np.array([buffer_line])
                sample          = np.transpose(sample)

                # Convert binary to voltage values
                for iBin in range(sample.size):
                    sample[iBin] = self.bin_to_voltage(sample[iBin])

                update_buffer   = np.concatenate((self.buffer, sample), axis=1)

                # Current timestamp -------------------------------------------
                time_stamp_now  = round(time.perf_counter() * 1000 - 
                    self.py_start, 4)
                time_stamps     = np.append(self.time_stamps, time_stamp_now)

                # Build new buffer and timestamp arrays
                self.buffer     = update_buffer[:, 1:]
                self.time_stamps= time_stamps[1:]

                # Filter buffer signal and send filtered data to plotting funcs
                # -------------------------------------------------------------
                processed_buffer = self.prepare_buffer()
                pipe_conn.send(processed_buffer)

            # Write out samples to file -----------------------------------
            if self.sample_count == self.saving_interval:

                self.calc_sample_rate()

                self.master_write_data(self.buffer, self.time_stamps, 
                    self.saving_interval, self.output_file)
                self.sample_count   = 0
                self.time_reset     = self.time_stamps[-1]


    def master_write_data(self, eeg_data, time_stamps, saving_interval,
        output_file):
        # =================================================================
        # Input:
        #   eeg_data            2D numpy array [channels x samples] (float)
        #   time_stamps         1D numpy array (float)
        #   saving_interval     Scalar
        #   output_file         Character string
        # Output:
        #   No output
        # =================================================================
        new_buffer          = eeg_data[:, -saving_interval:]
        new_time_stamps     = time_stamps[-saving_interval:]
            
        save_thread = Thread(target=self.write_data_thread,
            args=(new_buffer, new_time_stamps, output_file))
        save_thread.start()


    def calc_sample_rate(self):

        time_diff           = self.time_stamps[-1] - self.time_reset
        # It took (time_diff) ms to fetch (sample_rate) samples.
        # Calculate actual sampling rate
        actual_sr           = self.sample_rate / (time_diff / 1000)
        print('%d ms: Writing data (sampling rate = %f Hz)' %
            (self.time_stamps[-1], actual_sr))


    def write_data_thread(self, eeg_data, time_stamps, output_file):
        # =================================================================
        # Input:
        #   eeg_data            2D numpy array [channels x samples] (float)
        #   time_stamps         1D numpy array (float)
        #   output_file         Character string
        # Output:
        #   No output
        # =================================================================
        # Append the data points to the end of the file
        with open(output_file, 'a', encoding= "utf_8") as file:
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