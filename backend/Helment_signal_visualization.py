import time
import keyboard
import parameters                   as p
import numpy                        as np
import matplotlib.pyplot            as plt


class Plotting():

    def __init__(self):
        self.plot_intv  = p.plot_intv
        self.numchans   = p.buffer_channels
        self.samplerate = p.sample_rate
        self.numsamples = p.num_samples_vis
        self.yrange     = p.yrange
        self.plot_time  = 0


    def plot_samples(self, pipe_conn):
        # =================================================================
        # Input:
        #   iteration_timestamp Current timestamp (float)
        #   buffer              2D numpy array [channels x samples]
        # Output:
        #   No output
        # =================================================================
        fig, ax   = plt.subplots(self.numchans, 1,
            figsize=(15, 8), dpi=80)

        sampleplot     = {}
        for iChan in range(self.numchans):
            if iChan == 0:
                ax[iChan].set_title('Helment')
            elif iChan == self.numchans - 1:
                ax[iChan].set_xlabel('Time (s)')
            sampleplot[iChan], = ax[iChan].plot(
                np.array(range(0, self.numsamples, 1))/self.samplerate,
                np.zeros(self.numsamples), color='blue', linewidth=0.5)
            ax[iChan].set_ylabel('Amp. (uV)')
            ax[iChan].set_ylim(
                    bottom = self.yrange[0],
                    top = self.yrange[1],
                    emit = False, auto = False)
        plt.show(block=False)
        plt.pause(1)

        # get copy of entire figure (everything inside fig.bbox) sans animated artist
        bg = fig.canvas.copy_from_bbox(fig.bbox)
        # draw the animated artist, this uses a cached renderer
        for iChan in range(self.numchans):
            ax[iChan].draw_artist(sampleplot[iChan])

        # show the result to the screen, this pushes the updated RGBA buffer from the
        # renderer to the GUI framework so you can see it
        fig.canvas.blit(fig.bbox)

        while not keyboard.is_pressed('c'): # Alternatively "while True:"

            buffer = pipe_conn.recv()

            # Prepare plot window (the comma behind sampleplot is crucial)
            # -----------------------------------------------------------------
            current_time = round(time.perf_counter() * 1000, 4)
            # Skip if too soon
            if current_time <= self.plot_time + self.plot_intv:
                continue

            self.plot_time = current_time

            # reset the background back in the canvas state, screen unchanged
            fig.canvas.restore_region(bg)

            # Update plots for every channel
            # -------------------------------------------------------------
            for iChan in range(self.numchans):

                # signal      = scipy.signal.resample(buffer[iChan,], self.numsamples)
                signal      = buffer[iChan]
                sampleplot[iChan].set_ydata(signal) # Y values

                # re-render the artist, updating the canvas state, but not the screen
                ax[iChan].draw_artist(sampleplot[iChan])

            # Update plot time stamp and figure
            # -------------------------------------------------------------
            # copy the image to the GUI state, but screen might not be changed yet
            fig.canvas.blit(fig.bbox)
            # flush any pending GUI events, re-painting the screen if needed
            fig.canvas.flush_events()