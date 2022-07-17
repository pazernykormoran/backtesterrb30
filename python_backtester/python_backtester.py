
import asyncio
from libs.zmq.zmq import ZMQ
from libs.interfaces.python_backtester.trade import Trade
from libs.interfaces.python_backtester.money_state import MoneyState
from json import loads, dumps
from libs.data_feeds.data_feeds import DataSchema
from importlib import import_module
from libs.list_of_services.list_of_services import SERVICES, SERVICES_ARRAY
import pandas as pd
from os.path import join
import matplotlib.pyplot as plt
import time as tm

class Backtester(ZMQ):
    
    downloaded_data_path = '/var/opt/data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_module('strategies.'+self.config.strategy_name+'.data_schema').DATA
        
        self.main_instrument_chart = []
        # self.cumulated_money_chart: List[MoneyState] = []
        self.cumulated_money_chart = []
        self.trades = []

        self.number_of_actions = 0
        self.buy_summary_cost = 0
        self.sell_summary_cost = 0

        self.register("trade", self.__trade_event)
        self.register("data_finish", self.__data_finish_event)
        self.register("close_all_trades", self.__close_all_trades_event)

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

    def __get_main_instrument_chart(self):
        # load from csv
        pass
    
    def _trigger_event(self, event):
        pass
    
    def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                self._send(getattr(SERVICES, service), 'stop')
        self._stop()

    def __print_charts(self, finish_params):
        main_instrument_name = [element.symbol for element in self.data_schema.data if element.main == True][0]
        # print('main instrument name', main_instrument_name)
        files = [f for f in finish_params["file_names"] if main_instrument_name in f]
        # print('files', files)
        dfs = []
        for file in files:
            df = pd.read_csv(join(self.downloaded_data_path, file), index_col=None, header=None, names=['timestamp', 'price'])
            dfs.append(df)
        self.main_instrument_chart = pd.concat(dfs)

        #plot trades chart
        self.main_instrument_chart.plot(x ='timestamp', y='price', kind = 'line')	

        #plot money chart
        money_df = pd.DataFrame(self.cumulated_money_chart, columns=['timestamp', 'income'])
        money_df.plot(x ='timestamp', y='income', kind = 'line',)

        plt.show()

    def __trade(self, trade: Trade):
        self.trades.append([trade.timestamp, trade.price, trade.quantity])
        self.number_of_actions += trade.quantity
        if trade.quantity > 0: 
            self.buy_summary_cost += trade.quantity * trade.price
        else:
            self.sell_summary_cost += trade.quantity * trade.price
        local_income =  - self.buy_summary_cost - self.sell_summary_cost + self.number_of_actions * trade.price
        # print('lodal income', local_income)
        self.cumulated_money_chart.append([trade.timestamp, local_income])

        self._send(SERVICES.python_executor, 'set_number_of_actions', dumps(self.number_of_actions))


    # COMMANDS

    def __data_finish_event(self, finish_params):
        finish_params = loads(finish_params)
        finish_time = tm.time()
        time_of_backtest = finish_time - finish_params['start_time']
        self._log('')
        self._log('========================================================')
        self._log('BACKTEST FINISHED!!')
        self._log('time of backtest:', round(time_of_backtest,2), '[s]')
        self._log('number of trades:', len(self.trades))
        self._log('buy_summary_cost:', self.buy_summary_cost)
        self._log('sell_summary_cost:', self.sell_summary_cost)
        self._log('number of unrealized actions:', self.number_of_actions)
        self._log('actual price:', finish_params['main_instrument_price'])
        income = - self.buy_summary_cost - self.sell_summary_cost + self.number_of_actions * finish_params['main_instrument_price']
        self._log('income:', income)
        self._log('========================================================')
        self._log('')
        self.__print_charts(finish_params)
        self.__stop_all_services()

    def __trade_event(self, msg):
        trade: Trade = Trade(**loads(msg))
        self._log(f"Received trade: {trade}")
        self.__trade(trade)

    def __close_all_trades_event(self, msg):
        self._log(f"Received close all trades command")
        msg = loads(msg)
        msg["quantity"] = -self.number_of_actions
        trade: Trade = Trade(**msg)
        self.__trade(trade)


