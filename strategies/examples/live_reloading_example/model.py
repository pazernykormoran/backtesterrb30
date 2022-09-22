from libs.utils.model_imports import *

class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.state = {
            'counter': 0
        }
        self._set_buffer_length(200)
        self.live_reloading_module = self._add_reloading_module(
                self.config.strategy_path+'live_reloading/live_reloading.py')
        
    #override
    async def on_feed(self, data: list):
        await self.live_reloading_module.live_reloading_function(
                data, self.state, self._trigger_event, self._debug_breakpoint)

