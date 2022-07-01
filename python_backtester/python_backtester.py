
import asyncio
from typing import List
from libs.zmq.zmq import ZMQ
from libs.interfaces.python_backtester.trade import Trade
from libs.interfaces.python_backtester.money_state import MoneyState
from json import loads
from libs.data_feeds.data_feeds import DataSchema
from importlib import import_module
from libs.list_of_services.list_of_services import SERVICES, SERVICES_ARRAY

class Backtester(ZMQ):
    # override

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        
        self.main_instrument_chart = self.__get_main_instrument_chart()
        self.cumulated_money_chart: List[MoneyState] = []
        self.trades: List[Trade] = []

        self.number_of_actions = 0
        self.buy_summary_cost = 0
        self.sell_summary_cost = 0

        self.register("trade", self.__trade)
        self.register("data_finish", self.__data_finish)

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        self._create_listeners(loop)
        # loop.create_task(self._listen_zmq())
        loop.run_forever()
        loop.close()

    # override
    def _handle_zmq_message(self, message):
        pass


    def __data_finish(self, finish_params):
        finish_params = loads(finish_params)
        self._log('')
        self._log('========================================================')
        self._log('BACKTEST FINISHED!!')
        self._log('number of trades:', len(self.trades))
        self._log('buy_summary_cost:', self.buy_summary_cost)
        self._log('sell_summary_cost:', self.sell_summary_cost)
        self._log('number of unrealized actions:', self.number_of_actions)
        self._log('actual price:', finish_params['main_instrument_price'])
        income = - self.buy_summary_cost - self.sell_summary_cost + self.number_of_actions * finish_params['main_instrument_price']
        self._log('income:', income)
        self._log('========================================================')
        self._log('')
        self.__stop_all_services()

    def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                self._send(getattr(SERVICES, service), 'stop')
        self._stop()

    def __trade(self, msg):
        trade: Trade = Trade(**loads(msg))
        self._log(f"Received trade: {trade}")
        self.trades.append(trade)
        self.number_of_actions += trade.quantity
        if trade.quantity > 0: 
            self.buy_summary_cost += trade.quantity * trade.price
        else:
            self.sell_summary_cost += trade.quantity * trade.price

    def __get_main_instrument_chart(self):
        # load from csv
        pass
    
    def _trigger_event(self, event):
        pass