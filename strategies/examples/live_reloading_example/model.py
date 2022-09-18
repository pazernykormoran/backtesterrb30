from libs.utils.model_imports import *
from random import randint

async def live_reloading_function(data, state, _trigger_event, _debug_breakpoint):
    if state['counter'] % 30 == 0:
        quant = randint(-2,2)
        if quant != 0:
            message = {
                'value': quant
            }
            await _debug_breakpoint()
            _trigger_event(message)
    state['counter'] += 1


class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.state = {
            'counter': 0
        }
        self._set_buffer_length(200)
        self.live_reloading_module = self._add_reloading_module(
                'strategies.'+self.config.strategy_name+'.model')
        
    #override
    async def on_feed(self, data: list):
        await self.live_reloading_module.live_reloading_function(
                data, self.state, self._trigger_event, self._debug_breakpoint)

