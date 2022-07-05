from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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
    backtest_date_start: datetime
    backtest_date_stop: datetime
    data: List[DataSymbol]

"""
example of data:

data={
    'interval':STRATEGY_INTERVALS.hour,
    'backtest_date_start': datetime(2018,6,1),
    'data':[
        {
            'symbol': 'name1',
            'main': False
        },
        {
            'symbol': 'name2',
            'trigger_feed': False,
            'main': True,
        }
    ]
}
"""


#     # ustawiany jest interwał całej strategii. 
#     # dodawane są aktywa praktycznie dowolnie jeśli jakieś aktywno będzie miało za niski interwał to po prostu będzie próbkowane rzadziej. 
#     # przy interwale tick, tick każdego aktywa powoduje trigger chyba, że ustawisz mu triggers_feed na false.

