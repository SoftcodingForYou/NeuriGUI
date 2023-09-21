import scipy.signal
import numpy                        as np


class Processing():

    def __init__(self, parameters):

        self.pm                 = parameters
        self.prepare_filters()


    def prepare_filters(self):

        # Bandpass filters
        # -----------------------------------------------------------------
        self.b_detrend, self.a_detrend          = scipy.signal.butter(
            self.pm.filter_order, self.pm.frequency_bands["Whole"][0],
            btype='highpass', fs=self.pm.sample_rate)
        self.b_wholerange, self.a_wholerange    = scipy.signal.butter(
            self.pm.filter_order, self.pm.frequency_bands["Whole"],
            btype='bandpass', fs=self.pm.sample_rate)
        self.b_sleep, self.a_sleep              = scipy.signal.butter(
            self.pm.filter_order, self.pm.frequency_bands["Sleep"],
            btype='bandpass', fs=self.pm.sample_rate)
        self.b_theta, self.a_theta              = scipy.signal.butter(
            self.pm.filter_order, self.pm.frequency_bands["Theta"],
            btype='bandpass', fs=self.pm.sample_rate)
        self.b_notch, self.a_notch              = scipy.signal.butter(
            self.pm.filter_order, self.pm.frequency_bands["LineNoise"],
            btype='bandstop', fs=self.pm.sample_rate)
        self.b_notch60, self.a_notch60          = scipy.signal.butter(
            self.pm.filter_order, self.pm.frequency_bands["LineNoise60"],
            btype='bandstop', fs=self.pm.sample_rate)

        # Determine padding length for signal filtering
        # -----------------------------------------------------------------
        default_pad     = 3 * max(len(self.a_wholerange), 
            len(self.b_wholerange))
        if default_pad > self.pm.buffer_length * self.pm.sample_rate/10-1:
            self.padlen = int(default_pad) # Scipy expects int
        else:
            self.padlen = int(self.pm.buffer_length*self.pm.sample_rate/10-1) # Scipy expects int


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


    def extract_envelope(self, signal):
        hilbert         = signal
        for iChan in range(signal.shape[0]):
            # padded_signal   = np.pad(signal[iChan,], (self.padlen, self.padlen), 'symmetric')
            # hilbert[iChan,] = np.abs(scipy.signal.hilbert(padded_signal))[self.padlen:-self.padlen]
            hilbert[iChan,] = np.abs(scipy.signal.hilbert(signal[iChan,]))
        return hilbert


    def downsample(self, buffer, s_down):
        # =================================================================
        # Input:
        #   buffer              Numpy array [channels x samples]
        # Output:
        #   downsamples_buffer  Numpy array of downsampled signal, same  
        #                       dimensions as input buffer
        # =================================================================

        downsampled_signal  = np.zeros((buffer.shape[0], int(buffer.shape[1]/s_down)))
        idx_retain = range(0, buffer.shape[1], s_down)
        for iChan in range(self.pm.max_chans):
            # downsampled_signal[iChan,] = scipy.signal.decimate(buffer[iChan,], s_down)
            downsampled_signal[iChan,] = buffer[iChan,idx_retain]

        return downsampled_signal


    def prepare_buffer(self, buffer, bSB, aSB, bPB, aPB):
        # =================================================================
        # Input:
        #   buffer              Numpy array [channels x samples]
        #   bSB, aSB            Filter coefficients as put out by 
        #                       scipy.signal.butter (Stopband)
        #   bPB, aPB            Filter coefficients as put out by 
        #                       scipy.signal.butter (Passband)
        # Output:
        #   filtered_buffer     Numpy array of filtered signal, same  
        #                       dimensions as input buffer
        # =================================================================
        noise_free_signal   = np.zeros(buffer.shape)
        filtered_buffer     = np.zeros(buffer.shape)
        for iChan in range(self.pm.max_chans):

            # Reject ambiant electrical noise (at 50 Hz)
            # -------------------------------------------------------------
            if all(bSB != None):
                noise_free_signal[iChan,] = self.filter_signal(
                    buffer[iChan,], bSB, aSB)
            else:
                noise_free_signal[iChan,] = buffer[iChan,]

            # Extract useful frequency range
            # -------------------------------------------------------------
            if all(bPB != None):
                filtered_buffer[iChan,] = self.filter_signal(
                    noise_free_signal[iChan,], bPB, aPB)
            else:
                filtered_buffer[iChan,] = noise_free_signal[iChan,]

        return filtered_buffer