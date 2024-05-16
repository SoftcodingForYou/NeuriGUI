try:
    from compatible_boards import COMPATIBLE_BOARDS
except:
    from .compatible_boards import COMPATIBLE_BOARDS


class BoardAgnosticUtils():
        
    def __init__(self, parameter):

        # We can not just assign all parameters to for example self.params
        # since Python's Process() does not allow to parse several of the
        # stored objects in "parameters"
        self.streaming_parameter = {
            "baud_rate":    parameter.baud_rate,
            "time_out":     parameter.time_out,
            "port":         parameter.port,
            "start_code":   parameter.start_code, # Start code that boards reads as sign to startt sampling (int)
            "max_chans":    parameter.max_chans, # Specifies how many channels the incoming signals has (int)
            "buffer_length":parameter.buffer_length, # Length of constructed signal buffer (int)
            "buffer_add":   parameter.buffer_add, # Length of padding to avoid filter artifacts  (int)
            "sample_rate":  parameter.sample_rate, # Sampling rate (Hz, int)
            "PGA":          parameter.PGA, # Programmable gain (int)
            "saving_interval": parameter.saving_interval, # how often the data gets written to disk (seconds, int)
            "udp_ip":       parameter.udp_ip, # IP the data shall be forwarded to
            "udp_port":     parameter.udp_port, # Port of signal forwarding
            "set_customsession": parameter.set_customsession, # Whether or not to have a custom output file name (bool)
            "sessionName":  parameter.sessionName, # Custom file name for output (str)
        }


    def get_board_specific_utils(self, board):
        """Returns the board_specific functions that allows us to read and 
        process incoming signals

        Args:
            board (str): Unique name of board. Defined in parameters.py

        Returns:
            (object): Class object containing all necessary functions to
                work with given board.
        """
        for _, board_name in enumerate(list(COMPATIBLE_BOARDS.keys())):
            if board == board_name:
                return COMPATIBLE_BOARDS[board_name][3]
        raise Exception("Could not get board-specific functions collection")


    def headless_sampling(self):
        pass # This function only exists in order to make timer call something

    
         
