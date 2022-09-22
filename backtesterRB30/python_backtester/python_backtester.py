
import asyncio
from backtesterRB30.libs.interfaces.python_backtester.close_all_trades import CloseAllTrades
from backtesterRB30.libs.interfaces.python_backtester.data_start import DataStart
from backtesterRB30.libs.interfaces.python_backtester.debug_breakpoint import DebugBreakpoint
from backtesterRB30.libs.zmq.zmq import ZMQ
from backtesterRB30.libs.interfaces.python_backtester.trade import Trade
from backtesterRB30.libs.interfaces.python_backtester.money_state import MoneyState
from backtesterRB30.libs.interfaces.python_backtester.data_finish import DataFinish, CustomChart
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.utils.module_loaders import import_data_schema
from backtesterRB30.libs.utils.list_of_services import SERVICES, SERVICES_ARRAY
import pandas as pd
from os.path import join
import matplotlib.pyplot as plt
import time as tm
import numpy as np
from typing import List, Union
from datetime import datetime

class Backtester(ZMQ):
    
    downloaded_data_path = '/var/opt/data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_data_schema(self.config.strategy_path)
        
        self.main_instrument_chart = []
        # self.cumulated_money_chart: List[MoneyState] = []
        self.cumulated_money_chart = []
        self.trades = []

        self.number_of_actions = 0
        self.buy_summary_cost = 0
        self.sell_summary_cost = 0
        self.biggest_investment = 0
        self.__file_names = []
        self.__backtest_start_time = 0
        self.__fig = None
        self.__chart_displayed = False

        self._register("trade", self.__trade_event)
        self._register("data_finish", self.__data_finish_event)
        self._register("close_all_trades", self.__close_all_trades_event)
        self._register("data_start", self.__data_start_event)
        self._register("debug_breakpoint", self.__debug_breakpoint_event)

    # override
    def _loop(self):
        loop = asyncio.get_event_loop()
        self._create_listeners(loop)
        loop.create_task(self.__update_chart())
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
    
    async def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                super()._send(getattr(SERVICES, service), 'stop')
        super()._stop()

    async def __print_charts(self, file_names: List[str], 
                    custom_charts: List[CustomChart], 
                    last_timestamp: Union[int, None] = None):
        plt.close()
        if len(self.cumulated_money_chart) > 0:
            #plot trades chart
            number_of_custom_charts = 0
            if custom_charts != None:
                number_of_custom_charts = len([ch for ch in custom_charts if not ch.display_on_price_chart])

            #prepare axes
            self.__fig, axs = plt.subplots(nrows=2+number_of_custom_charts, ncols=1, sharex = True)

            # plot instrment chart
            main_chart = self.main_instrument_chart
            if last_timestamp != None:
                main_chart = self.main_instrument_chart.loc[self.main_instrument_chart['timestamp'] <= last_timestamp]
            ax = main_chart.plot(x ='timestamp', y='price', kind = 'line', ax=axs[0])
            if self.data_schema.log_scale_valuation_chart:	
                ax.set_yscale('log')
            normalized_quants = self.__normalize([abs(trade[2]) for trade in self.trades], (5,15))   
            for trade, quant in zip(self.trades, normalized_quants):
                ax.plot(trade[0], trade[1], '.g' if trade[2]>0 else '.r', ms=quant)
            
            #plot money chart
            money_df = pd.DataFrame(self.cumulated_money_chart, columns=['timestamp', 'income'])
            money_df.plot(x ='timestamp', y='income', kind = 'line', ax=axs[1], sharex = ax)

            #plot custom charts
            if custom_charts != None:
                for i, ch in enumerate(custom_charts):
                    chart = [[c.timestamp, c.value] for c in ch.chart ]
                    custom_df = pd.DataFrame(chart, columns=['timestamp', ch.name])
                    if ch.display_on_price_chart:
                        custom_df.plot(x ='timestamp', y=ch.name, kind = 'line', ax=axs[0], sharex = ax, color = ch.color)
                    else:
                        ax = custom_df.plot(x ='timestamp', y=ch.name, kind = 'line', ax=axs[2+i], sharex = ax, color = ch.color)
                        if ch.log_scale:
                            ax.set_yscale('log')
            if self.__chart_displayed == False:
                plt.ion()
                plt.show(block = False)
                self.__chart_displayed = True

    async def __update_chart(self): 
        while True:
            if self.__fig != None:
                try:
                    self.__fig.canvas.draw()
                    self.__fig.canvas.flush_events()
                except Exception as e: 
                    pass
            await asyncio.sleep(0.1)

    def __normalize(self, x, newRange=(0, 1)): #x is an array. Default range is between zero and one
        if len(x) == 0:
            return []
        xmin, xmax = np.min(x), np.max(x) #get max and min from input array
        if xmin != xmax:
            norm = (x - xmin)/(xmax - xmin) # scale between zero and one

            if newRange == (0, 1):
                return(norm) # wanted range is the same as norm
            elif newRange != (0, 1):
                return norm * (newRange[1] - newRange[0]) + newRange[0] #scale to a different range.
            #add other conditions here. For example, an error messag
        return np.ones_like(x) * 15


    def __trade(self, trade: Trade):
        self.trades.append([trade.timestamp, trade.price, trade.quantity])
        self.number_of_actions += trade.quantity
        if trade.quantity > 0: 
            self.buy_summary_cost += trade.quantity * trade.price
        else:
            self.sell_summary_cost += trade.quantity * trade.price
        local_income =  - self.buy_summary_cost - self.sell_summary_cost + self.number_of_actions * trade.price
        if abs(trade.price* self.number_of_actions) > self.biggest_investment:
            self.biggest_investment = abs(trade.price* self.number_of_actions)
        # print('lodal income', local_income)
        self.cumulated_money_chart.append([trade.timestamp, local_income])

        super()._send(SERVICES.python_executor, 'set_number_of_actions', self.number_of_actions)

    async def __print_summary(self, 
                custom_charts: List[CustomChart], 
                file_names: List[str],
                main_instrument_price: float,
                last_timestamp: Union[int, None] = None):
        self._log('==========================')
        self._log(('BREAKPOINT ' if last_timestamp != None else '') + 'SUMMARY')
        finish_time = tm.time()
        time_of_backtest = finish_time - self.__backtest_start_time
        self._log('time of backtest:', round(time_of_backtest,2), '[s]')
        self._log('number of trades:', len(self.trades))
        self._log('buy_summary_cost:', self.buy_summary_cost)
        self._log('sell_summary_cost:', self.sell_summary_cost)
        self._log('number of unrealized actions:', self.number_of_actions)
        self._log('biggest investment: ', self.biggest_investment)
        self._log('actual price:', main_instrument_price)
        income = - self.buy_summary_cost - self.sell_summary_cost + self.number_of_actions * main_instrument_price
        self._log('income:', income)
        self._log('==========================')
        self._log('')
        await self.__print_charts(file_names, custom_charts, last_timestamp)

    # COMMANDS

    async def __data_finish_event(self, finish_params):
        finish_params = DataFinish(**finish_params)
        self._log('')
        self._log('====================================================')
        self._log('BACKTEST FINISHED')
        await self.__print_summary(finish_params.custom_charts, 
                    self.__file_names, 
                    finish_params.main_instrument_price)
        self._log('====================================================')
        plt.show(block = True)
        await self.__stop_all_services()

    async def __trade_event(self, msg):
        trade: Trade = Trade(**msg)
        self._log(f"Received trade: timestamp={datetime.fromtimestamp(trade.timestamp/1000)}, quantity={trade.quantity}, price={trade.price}")
        self.__trade(trade)

    async def __close_all_trades_event(self, msg):
        self._log(f"Received close all trades command")
        msg = CloseAllTrades(**msg)
        msg = dict(msg)
        msg["quantity"] = -self.number_of_actions
        trade: Trade = Trade(**msg)
        self.__trade(trade)

    async def __data_start_event(self, start_params):
        start_params = DataStart(**start_params)
        self.__file_names = start_params.file_names
        self.__backtest_start_time = start_params.start_time
        main_instrument_name = [element.symbol for element in self.data_schema.data if element.main == True][0]
        files = [f for f in self.__file_names if main_instrument_name in f]
        dfs = []
        for file in files:
            df = pd.read_csv(join(self.downloaded_data_path, file), index_col=None, header=None, names=['timestamp', 'price'])
            dfs.append(df)
        self.main_instrument_chart = pd.concat(dfs)

    async def __debug_breakpoint_event(self, breakpoint_params):
        breakpoint_params = DebugBreakpoint(**breakpoint_params)
        await self.__print_summary(breakpoint_params.custom_charts, 
                    self.__file_names, 
                    breakpoint_params.main_instrument_price,
                    breakpoint_params.last_timestamp)


