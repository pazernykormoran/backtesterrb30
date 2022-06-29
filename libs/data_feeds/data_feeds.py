from enum import Enum
from pydantic import BaseModel
from typing import Optional, List

class STRATEGY_INTERVALS(Enum):
    tick='tick'
    second='second'
    minute='minute'
    minute15='minute15'
    minute30='minute30'
    hour='hour'
    day='day'
    week='week'
    month='month'


class DataSymbol(BaseModel):
    symbol: str
    trigger_feed: Optional[bool]
    main: Optional[bool]


class DataSchema(BaseModel):
    interval: STRATEGY_INTERVALS
    data: List[DataSymbol]

"""
example of data:

data={
    'interval':STRATEGY_INTERVALS.hour,
    'data':[
        {
            'symbol': 'name1',
            'trigger_feed': True,
        },
        {
            'symbol': 'name1',
            'trigger_feed': False,
            'main': True
        }
    ]
}
"""



# class IntervalConfigurator:

#     strategy_interval: STRATEGY_INTERVALS

#     def set_strategy_interval(self, interval: STRATEGY_INTERVALS):
#         self.strategy_interval = interval
#         """
#         how often the feed function is called:
#         if tick - strategy is triggered only basing on data feeds and "trigger_feed" variable on every instrment. 
#                     default trigger_feed is true for all instruments but you can set if manualy for every instrument.
#                     if its trigger_feed is set to false for any instrument, its not triggering sent bys its last value is sent while other triggers.
#         if regular interval - strategy is triggered only on regular interval.
#                     default trigger_feed is false for all instruments but you can set it manually for every instrument.
#                     if you set trigger_feed to true for any instrument, every tick of change will trigger new send.
#                     it can be usefull with rare but important data.
#         """


#     def add_symbol(self, name: str, trigger_feed: bool=False, main: bool=False):
#         """
#         names you can find in...
#         """
#         if self.strategy_interval:
#             if self.strategy_interval != STRATEGY_INTERVALS.tick:
#                 self.get_interval_symbol(name, self.strategy_interval)
#             else:
#                 self.get_interval_symbol(name, STRATEGY_INTERVALS.tick)
#         else:
#             print('error, exiting')
#             #TODO


#     def get_interval_symbol(self):
#         """
#         add to json config
#         """
#         pass
            
#     # dane live będą po prostu subowały live ceny i będzie wysyłana aktualna ramka, nie żadne świece. będzie to nawet łatwiejsze niż dane historyczne. 
#     # z danych.

#     # Defaultowo jest stały interwał. można natomiast to każdej danej dopisać aby jej feed triggerował osobne wysłanie. 


#     # ustawiany jest interwał całej strategii. 
#     # dodawane są aktywa praktycznie dowolnie jeśli jakieś aktywno będzie miało za niski interwał to po prostu będzie próbkowane rzadziej. 
#     # przy interwale tick, tick każdego aktywa powoduje trigger chyba, że ustawisz mu triggers_feed na false.

