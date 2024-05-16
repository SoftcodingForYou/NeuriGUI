from json import loads, dumps, decoder
from time import sleep, perf_counter
from numpy import expand_dims, concatenate, fromiter, append, array, zeros, reshape
try:
    from io_manager import IOManager
except:
    from .io_manager import IOManager
    

class SamplingUtilsNeuriLolinHelment():

    def __init__(self):
        pass # Necessary init function because we call attributes of this class in process_samples()
    

    def bin_to_voltage(self, s_bin, pga):
        # =================================================================
        # Convert binary into volts
        # Input
        #   s_bin       Float (binary) (crucial to be float, otherwise the 
        #               output "voltage" will be integer event if 
        #               method returns voltage as float)
        #   pga         Programmable gain (int)
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
    

    def message_to_samples(self, str_message, s_chans):
        # -----------------------------------------------------------------
        # Extract samples from board
        # Input
        #   str_message (str) Raw message string coming from board
        #   s_chans     (int) How many channels shall the samples be 
        #               assigned to
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
    

    def empty_message_queue(self, receiver):
        # TODO: Implement a cleaner way of flushing the port queue.
        # Officially supported flush functions in pyserial do not
        # seem to have effect.
        receiver.flush()
        receiver.reset_input_buffer()
        receiver.reset_output_buffer()

        # Implement dirty method:
        for _ in range(1,000):
            receiver.read(receiver.inWaiting())
        
    
    def setup_neuri_board(self, receiver, start_code):
        self.empty_message_queue(receiver)
        receiver.write(bytes(str(start_code), 'utf-8'))
        board_booting = True
        print('Board is booting up ...')
        while board_booting:
            raw_message = str(receiver.readline())
            print(raw_message)
            if 'Listening ...' in raw_message:
                receiver.write(bytes(str(start_code), 'utf-8')) # Try again
                sleep(1)
            elif '{' in raw_message and '}' in raw_message:
                print('Fully started')
                board_booting = False


    def process_samples(self, transmitter, parameter, shared_buffer,
                     shared_timestamp, gui_running):

        io_manager = IOManager(parameter)
        receiver = io_manager.set_up_serial_entry_point(
            parameter["baud_rate"], parameter["time_out"], parameter["port"])

        with receiver as r:

            # Open communication ----------------------------------------------
            sleep(1)

            self.setup_neuri_board(r, parameter["start_code"])
            if parameter["start_code"] == 2:
                s_per_buffer    = 1
                print('Ordered board to send data via USB. Switching mode ...')
            elif parameter["start_code"] == 3:
                s_per_buffer    = 10
                print('Ordered board to send data via Bluetooth. Switching mode ...')

            # Prealloate values of loop ---------------------------------------
            start_time          = int(perf_counter() * 1000)
            time_stamp_now      = int(perf_counter() * 1000) # Do NOT copy from start_time (will generate pointer)
            time_reset          = int(perf_counter() * 1000) # Do NOT copy from start_time (will generate pointer)
            sample_count        = int(0)
            
            buffer              = zeros((parameter["max_chans"],
                (parameter["buffer_length"] + parameter["buffer_add"]) * parameter["sample_rate"]))
            time_stamps         = zeros(parameter["buffer_length"] * parameter["sample_rate"], dtype=int)
            pga                 = parameter["PGA"]
            s_chans             = parameter["max_chans"]
            sampling_rate       = parameter["sample_rate"]
            saving_interval     = parameter["saving_interval"] * parameter["sample_rate"]
            update_buffer       = zeros((buffer.shape[0], buffer.shape[1]+1))
            update_times        = zeros((buffer.shape[1]+1), dtype=int)

            # Preallocate json relay message and relay connection
            relay_array         = io_manager.build_standard_relay_message(parameter["max_chans"])
            udp_ip              = parameter["udp_ip"]
            udp_port            = parameter["udp_port"]

            self.empty_message_queue(r)
                
            while gui_running.value == 1:
                
                raw_message             = str(r.readline())

                buffer_in, valid_eeg    = self.message_to_samples(raw_message, s_chans)

                if not valid_eeg:
                    # TODO: Implement an interpolation system
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

                    # Write out samples to file -----------------------------------
                    if sample_count == saving_interval:

                        io_manager.calc_sample_rate(time_stamp_now, time_reset, 
                                            sampling_rate, time_stamps)

                        io_manager.master_write_data(buffer, time_stamps, 
                            saving_interval)
                        sample_count        = 0
                        time_reset          = time_stamp_now

            r.write(bytes(str(0), 'utf-8')) # Set board into standby
            sleep(1)
            return