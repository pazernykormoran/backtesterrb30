
from libs.utils.model_imports import *
from random import randint

class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.counter = 0
        self._set_buffer_length(2)

    #override
    async def on_feed(self, data: list):
        if self.counter % 10 == 0:
            quant = randint(-2,2)
            if quant != 0:
                message = {
                    'value': quant
                }
                self._trigger_event(message)
                await self._debug_breakpoint()
        self.counter += 1
