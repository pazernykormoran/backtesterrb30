from libs.necessery_imports.data_imports import *

# configure data feed =====================================

data={
    'interval':STRATEGY_INTERVALS.hour,
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
DATA = DataSchema(**data)
