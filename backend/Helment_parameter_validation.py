class ParamVal():

    def __init__(self, p):

        self.verify_compatibility(p)


    def verify_compatibility(self, p):

        if p.saving_interval > p.buffer_length: #Checkpoint of parameters
            raise Exception('Buffer can not be shorter than saving interval')
        
        if len([i for i in range(p.max_chans) if p.selected_chans[i]]) == 0:
            raise Exception('No channel selected for display. Please select at least one')