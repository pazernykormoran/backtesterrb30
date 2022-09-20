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

