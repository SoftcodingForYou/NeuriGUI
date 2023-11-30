from json import loads, dumps, decoder
from time import sleep, perf_counter
#import random
from numpy import expand_dims, concatenate, fromiter, append, array, zeros, reshape
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

        # Prepare data output
        self.output_file= file_name

        with open(self.output_file, 'w', encoding= "utf_8") as file:
            file.write("Session Started\n")
            file.close() # Important for data to get written


    def bin_to_voltage(self, s_bin, pga):
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
        
        voltage = (4.5*sign_bit)/(pga*8388607.0)
        voltage = voltage * 1000000 # Convert to microvolts

        #voltage = random.randrange(-200, 200)
        return voltage
    

    def channel_assignment(self, str_message, s_chans):
        # -----------------------------------------------------------------
        # Extract samples from board
        # Input
        #   str_message Raw message string coming from board
        # Default in case of faulty message
        eeg_array       = expand_dims(
            array([0] * s_chans, dtype=float), # Crucial to set float
            axis=1)
        eeg_valid       = False
        #   eeg_array   Numpy array (floats), being channels by samples
        #   eeg_valid   Boolean whether workable data or not
        # -----------------------------------------------------------------

        str_message     = str_message[
            str_message.find('{'):str_message.find('}')+1]
        
        # Build Python dictionnary
        try:
            chanDict        = loads(str_message)
        except decoder.JSONDecodeError:
            # Corrupt message: not all channels present
            print("Skipped message")
            return eeg_array, eeg_valid

        if len(chanDict) != s_chans:
            return eeg_array, eeg_valid
        
        eeg_array       = expand_dims(
            fromiter(chanDict.values(), dtype=float), # Crucial to set float
            axis=1)
        eeg_valid       = True
        
        return eeg_array, eeg_valid


    def fetch_sample(self, receiver, transmitter, parameter, shared_buffer, shared_timestamp, gui_running):

        if parameter.firmfeedback == 2: # USB
            s_per_buffer    = 1
            print('Ordered board to send data via USB. Switching mode ...')
        elif parameter.firmfeedback == 3: # Bluetooth
            s_per_buffer    = 10
            print('Ordered board to send data via Bluetooth. Switching mode ...')

        if receiver.port == '':
            raise Exception('Verify that desired connection type (USB or Bluetooth) are indeed available')

        with receiver as r:

            # Open communication ----------------------------------------------
            sleep(1)

            # TO-DO: These functions below do not empty the buffer at the 
            # port as they are supposed to do
            r.flush()
            r.reset_input_buffer()
            r.reset_output_buffer()

            r.write(bytes(str(parameter.firmfeedback), 'utf-8'))
            # time.sleep(1)

            board_booting = True
            print('Board is booting up ...')
            while board_booting:
                raw_message = str(r.readline())
                print(raw_message)
                if 'Listening ...' in raw_message:
                    r.write(bytes(str(parameter.firmfeedback), 'utf-8')) # Try again
                    sleep(1)
                elif '{' in raw_message and '}' in raw_message:
                    print('Fully started')
                    board_booting = False


            # Prealloate values of loop ---------------------------------------
            start_time          = int(perf_counter() * 1000)
            time_stamp_now      = int(perf_counter() * 1000) # Do NOT copy from start_time (will generate pointer)
            time_reset          = int(perf_counter() * 1000) # Do NOT copy from start_time (will generate pointer)
            sample_count        = int(0)
            
            buffer              = zeros((parameter.max_chans, 
                (parameter.buffer_length + parameter.buffer_add) * parameter.sample_rate))
            time_stamps         = zeros(parameter.buffer_length * parameter.sample_rate, dtype=int)
            pga                 = parameter.PGA
            s_chans             = parameter.max_chans
            sampling_rate       = parameter.sample_rate
            saving_interval     = parameter.saving_interval * parameter.sample_rate
            update_buffer       = zeros((buffer.shape[0], buffer.shape[1]+1))
            update_times        = zeros((buffer.shape[1]+1), dtype=int)

            # Preallocate json relay message and relay connection
            relay_array         = {}
            relay_array["t"]    = ''
            for iC in range(s_chans):
                relay_array["".join(["c", str(iC+1)])] = ''
            udp_ip              = parameter.udp_ip
            udp_port            = parameter.udp_port

            for _ in range(1,000):
                r.read(r.inWaiting())
                # Eliminate message queue at port, do this several times to get
                # everything since buffer that we get with inWaiting is limited
                
            while gui_running.value == 1:
                
                raw_message             = str(r.readline())

                buffer_in, valid_eeg    = self.channel_assignment(raw_message, s_chans)

                if not valid_eeg:
                    # TO-DO: Implement an interpolation system
                    continue

                # Current timestamp -------------------------------------------
                time_stamp_now          = int(perf_counter() * 1000) - start_time
                # This will generate unchanged time_stamps for all samples of 
                # the incoming bufer (= 10 in case of bluetooth), but that is
                # not a problem

                # Each channel carries self.s_per_buffer amounts of samples 
                # (theoretically). Since parts of messages can be lost, we 
                # soft-set the amount of samples after checking for data 
                # integrity during data_checkpoint()
                for iS in range(s_per_buffer):

                    sample_count        = sample_count + 1
                    
                    sample              = buffer_in[:, iS]

                    # Convert binary to voltage values
                    for iBin in range(s_chans):
                        sample[iBin]    = self.bin_to_voltage(sample[iBin], pga)
                        relay_array["".join(["c", str(iBin+1)])] = str(sample[iBin])

                    update_buffer       = concatenate((buffer, expand_dims(sample, 1)), axis=1)
                    update_times        = append(time_stamps, time_stamp_now)

                    # Build new buffer and timestamp arrays
                    buffer              = update_buffer[:, 1:]
                    time_stamps         = update_times[1:]

                    # Make data available for downstream programs
                    transmitter.sendto(bytes(dumps(relay_array), "utf-8"), (udp_ip, udp_port))

                    # Update shared memory allocations for frontend
                    shared_buffer[:] = reshape(buffer, buffer.size) # Has left edge for filtering
                    shared_timestamp.value = time_stamp_now
                    # pipe_conn.put((buffer, time_stamp_now))

                    # Write out samples to file -----------------------------------
                    if sample_count == saving_interval:

                        self.calc_sample_rate(time_stamp_now, time_reset, 
                                            sampling_rate, time_stamps)

                        self.master_write_data(buffer, time_stamps, 
                            saving_interval, self.output_file)
                        sample_count        = 0
                        time_reset          = time_stamp_now

            r.write(bytes(str(0), 'utf-8')) # Set board into standby
            sleep(1)
            return


    def headless_sampling(self, shared_buffer, shared_timestamp):
        # Python's multiprocessing's Pipe() is sending and receiving data 
        # in blocking mode. That means if a sender is putting data in the 
        # memory buffer, but no consumer is receiving it, the sending of 
        # data is blocked until the buffer is emptied. This here is a 
        # pseudo-sampling function purely designed to empty the buffer.
        pass


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


    def calc_sample_rate(self, curr_time, prev_iter_time, sample_rate, time_stamps):

        time_diff           = curr_time - prev_iter_time
        # It took (time_diff) ms to fetch (sample_rate) samples.
        # Calculate actual sampling rate
        actual_sr           = int((sample_rate / (time_diff / 1000)))
        print('%d ms: Writing data (sampling rate = %d Hz)' %
            (time_stamps[-1], actual_sr))


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