from typing import List

from pydantic import BaseModel


class Position(BaseModel):
    number_of_actions: float = 0
    position_outcome: float = 0
    buy_summary_cost: float = 0
    sell_summary_cost: float = 0
    last_instrument_price: float = 0
    trades: List = []
