class ParamVal():

    def __init__(self, p):

        self.verify_compatibility(p)


    def verify_compatibility(self, p):

        if p.saving_interval > p.buffer_length: #Checkpoint of parameters
            raise Exception('Buffer can not be shorter than saving interval./nThis is a developer error and not your responsability as a user. Please contact the developers.')
        
        if len([i for i in range(p.max_chans) if p.selected_chans[i]]) == 0:
            raise Exception('No channel selected for display. Please select at least one.')
        
        if len(p.sessionName) == 0:
            raise Exception('You set a custom name for the session but there were no characters.')
        
        if p.sample_rate < 100:
            raise Exception('Sampling rate too low. Set a rate of at least 100 Hz.')

        if len(p.port) == 0:
            raise Exception('No device set to connect to. Chose a valid COM port.')