import parameters as p

class ParamVal():

    def __init__(self):

        self.verify_compatibility()


    def verify_compatibility(self):

        if p.saving_interval > p.buffer_length: #Checkpoint of parameters
            raise Exception('Buffer can not be shorter than saving interval')