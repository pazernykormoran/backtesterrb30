

from pydantic import BaseModel, validator
from typing import List, Any
from pandas import DataFrame
from backtesterRB30.libs.interfaces.python_backtester.trade import Trade
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol

class Position(BaseModel):
    number_of_actions: float = 0
    position_outcome: float = 0
    buy_summary_cost: float = 0
    sell_summary_cost: float = 0
    last_instrument_price: float = 0
    trades: List = []
