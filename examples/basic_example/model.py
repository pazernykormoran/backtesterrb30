import backtesterRB30 as bt
from random import randint

class Model(bt.Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.counter = 0
        self.set_buffer_length(200)

    #override
    async def on_feed(self, data: list):
        if self.counter % 30 == 0:
            quant = randint(-2,2)
            if quant != 0:
                message = {
                    'value': quant
                }
                self.trigger_event(message)
        self.counter += 1

