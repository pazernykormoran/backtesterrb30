from random import randint

async def live_reloading_function(data, state, _trigger_event, debug_breakpoint):
    if state['counter'] % 100 == 0:
        quant = randint(-2,2)
        if quant != 0:
            message = {
                'value': quant
            }
            await debug_breakpoint(False)
            await _trigger_event(message)
    state['counter'] += 1

