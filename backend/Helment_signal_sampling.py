import json
import time
import socket
#import random
import numpy                            as np
from threading                          import Thread
from datetime                           import datetime


class Sampling():

    def __init__(self, parameter):

        #Output
        t0              = str(datetime.now())
        t0              = t0.replace(':', '_')
        if parameter.set_customsession:
            file_name   = parameter.sessionName + '.txt'
        else:
            file_name   = 'Helment ' + t0 + '.txt'

        self.py_start   = round(time.perf_counter() * 1000, 0)
        self.pga        = parameter.PGA

        # Prepare data output
        self.output_file= file_name
        self.buffer     = np.zeros((parameter.max_chans, 
            (parameter.buffer_length + parameter.buffer_add) * parameter.sample_rate))
        self.time_stamps= np.zeros(parameter.buffer_length * parameter.sample_rate)

        with open(self.output_file, 'w', encoding= "utf_8") as file:
            file.write("Session Started\n")
            file.close() # Important for data to get written

        # Sample fetching parameters
        self.sample_count       = parameter.sample_count # From parameters
        self.saving_interval    = parameter.saving_interval * parameter.sample_rate # From parameters
        self.time_reset         = self.py_start
        self.sample_rate        = parameter.sample_rate
        self.s_chans            = parameter.max_chans

        # Build relay connection for other programs
        self.build_relay(parameter.udp_ip)


    def build_relay(self, ip):
        # =================================================================
        # This connection will be used in order to transfer the incoming 
        # signal from the board to a dynamuically defined port via UDP
        # =================================================================

        self.udp_port   = self.search_free_com(ip)
        self.udp_ip     = ip
        self.send_sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        print('Relay connection established at ' + self.udp_ip + ':' + str(self.udp_port))
        print('Use this connection to import signals in your own program!\n')
    

    def search_free_com(self, ip):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for iPort in range(12344, 12350):
            try:
                s = s.connect((ip, iPort))
            except:
                return iPort

        raise Exception('No available UDP port found for signal relay')


    def bin_to_voltage(self, s_bin):
        # =================================================================
        # Convert binary into volts
        # Input
        #   s_bin       Float (binary) (crucial to be float, otherwise the 
        #               output "voltage" will be integer event if 
        #               method returns voltage as float)
        # Output
        #   - voltage   Float (microvolts)
        # =================================================================
        s_bin       = int(s_bin) # requieres int
        sign_bit    = 0
        if s_bin == 0:
            return 0
        if s_bin > 0 and s_bin <= 8388607:
            sign_bit = s_bin
        elif s_bin > 8388607 and s_bin <= 2*8388607:
            sign_bit = -2*8388607 + s_bin - 1
        else:
            print('sign_bit not assigned, returning 0')
        
        voltage = (4.5*sign_bit)/(self.pga*8388607.0)
        voltage = voltage * 1000000 # Convert to microvolts

        #voltage = random.randrange(-200, 200)
        return voltage
    

    def channel_assignment(self, str_message):
        # -----------------------------------------------------------------
        # Extract samples from board
        # Input
        #   str_message Raw message string coming from board
        # Default in case of faulty message
        eeg_array       = np.expand_dims(
            np.array([0] * self.s_chans, dtype=float), # Crucial to set float
            axis=1)
        eeg_valid       = False
        #   eeg_array   Numpy array (floats), being channels by samples
        #   eeg_valid   Boolean whether workable data or not
        # -----------------------------------------------------------------

        str_message     = str_message[
            str_message.find('{'):str_message.find('}')+1]
        
        # Build Python dictionnary
        try:
            chanDict        = json.loads(str_message)
        except json.decoder.JSONDecodeError:
            # Corrupt message: not all channels present
            print("Skipped message")
            return eeg_array, eeg_valid

        if len(chanDict) != self.s_chans:
            return eeg_array, eeg_valid
        
        eeg_array       = np.expand_dims(
            np.fromiter(chanDict.values(), dtype=float), # Crucial to set float
            axis=1)
        eeg_valid       = True
        
        return eeg_array, eeg_valid


    def fetch_sample(self, pipe_conn, ser, cons, desired_con):

        if desired_con == 2: # USB
            s_per_buffer    = 1
            print('Ordered board to send data via USB. Switching mode ...')
        elif desired_con == 3: # Bluetooth
            s_per_buffer    = 10
            print('Ordered board to send data via Bluetooth. Switching mode ...')

        # Open communication ----------------------------------------------
        if ser.port == '':
            raise Exception('Verify that desired connection type (USB or Bluetooth) are indeed available')
        else:
            ser.open()
            time.sleep(1)

        ser.write(bytes(str(desired_con), 'utf-8'))
        # time.sleep(1)

        board_booting = True
        print('Board is booting up ...')
        while board_booting:
            raw_message = str(ser.readline())
            print(raw_message)
            if 'Listening ...' in raw_message:
                ser.write(bytes(str(desired_con), 'utf-8')) # Try again
                time.sleep(1)
            elif '{' in raw_message and '}' in raw_message:
                print('Fully started')
                board_booting = False


        # Preallocate json relay message
        relay_array         = {}
        relay_array["t"]    = ''
        for iC in range(self.s_chans):
            relay_array["".join(["c", str(iC+1)])] = ''

        for _ in range(1000):
            ser.read(ser.inWaiting())
            # Eliminate message queue at port, do this several times to get
            # everything since buffer that we get with inWaiting is limited
            
        while not ser.closed:
            
            raw_message             = str(ser.readline())

            buffer_in, valid_eeg    = self.channel_assignment(raw_message)

            if not valid_eeg:
                # TO-DO: Implement an interpolation system
                continue

            # Current timestamp -------------------------------------------
            time_stamp_now          = round(
                time.perf_counter() * 1000, 0) - self.py_start
            # This will generate unchanged time_stamps for all samples of 
            # the incoming bufer (= 10 in case of bluetooth), but that is
            # not a problem

            # Each channel carries self.s_per_buffer amounts of samples 
            # (theoretically). Since parts of messages can be lost, we 
            # soft-set the amount of samples after checking for data 
            # integrity during data_checkpoint()
            for iS in range(buffer_in.shape[1]):

                self.sample_count   = self.sample_count + 1
                
                sample              = buffer_in[:, iS]

                # Convert binary to voltage values
                for iBin in range(sample.size):
                    sample[iBin]    = self.bin_to_voltage(sample[iBin])
                    relay_array["".join(["c", str(iBin+1)])] = str(sample[iBin])

                update_buffer       = np.concatenate((self.buffer, np.expand_dims(sample, 1)), axis=1)
                update_times        = np.append(self.time_stamps, time_stamp_now)

                # Build new buffer and timestamp arrays
                self.buffer         = update_buffer[:, 1:]
                self.time_stamps= update_times[1:]

                self.send_sock.sendto(bytes(json.dumps(relay_array), "utf-8"), (self.udp_ip, self.udp_port))

                pipe_conn.send((self.buffer, time_stamp_now))

                # Write out samples to file -----------------------------------
                if self.sample_count == self.saving_interval:

                    self.calc_sample_rate(time_stamp_now, self.time_reset)

                    self.master_write_data(self.buffer, self.time_stamps, 
                        self.saving_interval, self.output_file)
                    self.sample_count   = 0
                    self.time_reset     = time_stamp_now


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


    def calc_sample_rate(self, curr_time, prev_iter_time):

        time_diff           = curr_time - prev_iter_time
        # It took (time_diff) ms to fetch (sample_rate) samples.
        # Calculate actual sampling rate
        actual_sr           = round((self.sample_rate / (time_diff / 1000)), 1)
        print('%d ms: Writing data (sampling rate = %.1f Hz)' %
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