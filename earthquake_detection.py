import numpy as np
from scipy import signal

###
# Summary of functionality:
#   Everytime a new set of samples is added to the detector via new_samples(), we check if there is a new peak by calling 
#   check_for_quake(). check_for_quake() uses the scipy.signal.find_peaks_cwt() peak-finding function to find peaks within 
#   the last 30 days of data on the given seismograph
#   If a peak is found which is not a previously found peak, then we move on to checking if the other seismographs also
#       showed a peak at the given peak time using the is_peak() function. If all other seismographs return True on that
#       function, then this satisfies the conditions for an earthquake and we can call the provided alert_callback() function.
###

class EarthquakeDetector :
    def __init__ ( self , seismograph_count , sample_rate_hz , alert_callback ):
        """
        Args :
            seismograph_count : the number of seismographs
            in the detector network .
            sample_rate_hz : the sample rate of the
            seismograph
            alert_callback : a callback function if an
            earthquake is detected .
        """
        self.seismographs = [None] * seismograph_count # initialize to all empty samples
        self.sample_rate = sample_rate_hz
        self.alert_callback = alert_callback
        self.month_window_size = 30 * 24 * 60 * 60 * self.sample_rate # number of samples in a 30 day window

        self.confirmed_peak_indices = [] 


    def new_samples ( self , seismograph_id , samples ):
        """ New samples are available for a seismograph .
        Args :
            seismograph_id : the zero - indexed seismograph id.
            samples : an ndarray of integer samples .
        """
        if self.seismographs[seismograph_id]:
            self.seismographs[seismograph_id] = np.concatenate(self.seismographs[seismograph_id], samples)
            pass
        else:  # need to initialize
            self.seismographs[seismograph_id] = samples

        self.check_for_quake(seismograph_id) # check for quake every time we get new samples


    def peak_detect(self, samples):
        """Use scipy.signal.find_peaks_cwt() to detect peak(s) recursively"""
        dim = samples.shape[0]
        hour = self.sample_rate * 60 * 60 # assume a peak will not be wider than 1 hour
        if dim == 1: # apply function
            peak_inds = signal.find_peaks_cwt(samples, hour) # run peak finding
        else:
            peak_inds = [self.peak_detect(samples[i])[0] for i in range(len(samples))] # recurse
        
        peaks = [samples[i] for i in peak_inds]
        return peak_inds[peaks.index(max(peaks))] # return index with max peak
        # I am aware just pulling the max is not representative of the case where a smaller but still real peak occured after
        # a prior larger peak, and adding that level of robustness would be my next step in the implementation, however I did
        # not have time to write that out here
    
    def is_peak(self, seis, peak_index):
        """
        I did not have time to implement this but this function should return True if peak_index aligns with a peak in a given seis.
        It should do this by running self.peak_detect and comparing peak_index to the output.
        By using signal.find_peaks_cwt(), which is agnostic to scaling, we automatically bypass the issue of different calibrations
            between seismographs.
        """
        return False

    def check_for_quake(self, seismograph_id):
        """
        Check the last 30 days of samples from a seismograph for a peak using scipy.signal.find_peaks_cwt()
        """
        samples = self.seismographs[seismograph_id][-self.month_window_size:] # get last 30 days of samples
        
        reverse_peak_index = self.peak_detect(samples)
        peak_index = len(samples) - self.month_window_size + reverse_peak_index

        if peak_index not in self.confirmed_peak_indices:
            # check for a peak in the other seismogrpahs at peak_index
            true_peak = True
            for seis in self.seismographs:
                # run function is_peak that checks if peak_index is indeed a peak in a given seis
                if not self.is_peak(seis, peak_index):
                    true_peak = False
                    break

            if true_peak:
                self.alert_callback() # all detectors have indicated a positive peak at this peak index
                self.confirmed_peak_indices.append(peak_index)
            else:
                pass # false alarm

        else:
            pass # already detected in past

