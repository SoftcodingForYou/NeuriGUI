import scipy.signal
import parameters                   as p
import numpy                        as np


class Processing():

    def __init__(self):
        pass


    def prepare_filters(self):

        # Bandpass filters
        # -----------------------------------------------------------------
        self.b_wholerange, self.a_wholerange    = scipy.signal.butter(
            p.filter_order, p.frequency_bands["Whole"],
            btype='bandpass', fs=p.sample_rate)
        self.b_notch, self.a_notch              = scipy.signal.butter(
            p.filter_order, p.frequency_bands["LineNoise"],
            btype='stop', fs=p.sample_rate)

        # Determine padding length for signal filtering
        # -----------------------------------------------------------------
        default_pad     = 3 * max(len(self.a_wholerange), 
            len(self.b_wholerange))
        if default_pad > p.buffer_length/10-1:
            self.padlen = int(default_pad) # Scipy expects int
        else:
            self.padlen = int(p.buffer_length*p.sample_rate/10-1) # Scipy expects int
        self.padlen = int(p.buffer_length*p.sample_rate-1)


    def filter_signal(self, signal, b, a):
        # =================================================================
        # Input:
        #   signal              Numpy 1D array [samples]
        # Output:
        #   signal_filtered[0]  1D numpy array of filtered signal where 
        #                       first sample is 0
        # =================================================================
        padded_signal   = np.pad(signal, (self.padlen, 0), 'symmetric')
        init_state      = scipy.signal.lfilter_zi(b, a) # 1st sample --> 0
        signal_filtered = scipy.signal.lfilter(b, a, padded_signal, 
            zi=init_state*padded_signal[0])
        signal_filtered = signal_filtered[0][self.padlen:]
        return signal_filtered


    def prepare_buffer(self):
        # =================================================================
        # Input:
        #   buffer              Numpy array [channels x samples]
        # Output:
        #   filtered_buffer     Numpy array of filtered signal, same  
        #                       dimensions as input buffer
        # =================================================================
        spike_free_signal   = np.zeros(self.buffer.shape)
        noise_free_signal   = np.zeros(self.buffer.shape)
        filtered_buffer     = np.zeros(self.buffer.shape)
        for iChan in range(self.numchans):

            # Reject signal spikes (should only be apllied if necessary)
            # -------------------------------------------------------------
            # spike_free_signal[iChan,] = scipy.signal.medfilt(
            #     self.buffer[iChan,], kernel_size=3)

            spike_free_signal[iChan,] = self.buffer[iChan,]

            # Reject ambiant electrical noise (at 50 Hz)
            # -------------------------------------------------------------
            noise_free_signal[iChan,] = self.filter_signal(
                spike_free_signal[iChan,], self.b_notch, self.a_notch)

            # Extract useful frequency range
            # -------------------------------------------------------------
            filtered_buffer[iChan,] = self.filter_signal(
                noise_free_signal[iChan,], self.b_wholerange, 
                self.a_wholerange)

        return filtered_buffer