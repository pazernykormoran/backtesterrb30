import backtesterRB30 as bt
from os.path import join

class Model(bt.Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.state = {
            'counter': 0
        }
        self.set_buffer_length(200)
        self.live_reloading_module = self.add_reloading_module(
                join(self.config.strategy_path, 'live_reloading/live_reloading.py'))
        
    #override
    async def on_feed(self, data: list):
        await self.live_reloading_module.live_reloading_function(
                data, self.state, self.trigger_event, self.debug_breakpoint)

