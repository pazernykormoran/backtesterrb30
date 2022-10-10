
from abc import abstractmethod
import asyncio
from backtesterRB30.libs.communication_broker.broker_base import BrokerBase
from backtesterRB30.libs.interfaces.python_backtester.data_start import DataStart
from backtesterRB30.libs.interfaces.python_backtester.debug_breakpoint import DebugBreakpoint
from backtesterRB30.libs.interfaces.python_backtester.last_feed import LastFeed
from backtesterRB30.libs.interfaces.python_backtester.positions import Position
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterRB30.libs.communication_broker.zmq_broker import ZMQ
from backtesterRB30.libs.communication_broker.asyncio_broker import AsyncioBroker
from backtesterRB30.libs.interfaces.python_backtester.trade import Trade
from backtesterRB30.libs.interfaces.python_backtester.money_state import MoneyState
from backtesterRB30.libs.interfaces.python_backtester.data_finish import DataFinish, CustomChart
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema
from backtesterRB30.libs.utils.list_of_services import SERVICES, SERVICES_ARRAY
import pandas as pd
from os.path import join
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import time as tm
import numpy as np
from typing import List, Union
from datetime import datetime
from backtesterRB30.libs.utils.service import Service
from backtesterRB30.libs.interfaces.utils.config import Config, BROKERS
from appdirs import user_cache_dir

class Backtester(Service):
    
    downloaded_data_path = user_cache_dir('rb30_cache')
    _broker: BrokerBase

    def __init__(self, config: Config, data_schema: DataSchema, loop = None, logger=print):
        super().__init__(config, logger)
        self.config: Config=config
        self.__loop =  loop
        self.__custom_event_loop = False
        if self.__loop == None: 
            self.__loop = asyncio.get_event_loop()
            self.__custom_event_loop= True
        self.data_schema: DataSchema = data_schema
        for dat in self.data_schema.data:
            dat.additional_properties['position'] = None
            dat.additional_properties['chart_data_frame'] = None
        
        # self.trading_instruments_charts = []
        self.cumulated_money_chart = []
        # self.positions: List[Position] = []
        self.__last_feed: LastFeed = {}
        self.__last_timestamp: int = 0

        self.__backtest_start_time = 0
        self.__fig = None
        self.__chart_displayed = False



    # # override
    # def _asyncio_loop(self, loop: asyncio.AbstractEventLoop):
    #     self._create_listeners(loop)
    #     loop.create_task(self.__update_chart())

    # # override
    # def _handle_zmq_message(self, message):
    #     pass

    def _loop(self):
        # self._broker.run()
        self._broker.create_listeners(self.__loop)
        self.__loop.create_task(self.__update_chart())
        if self.__custom_event_loop:
            self.__loop.run_forever()
            self.__loop.close()

    # def _send(self, service: SERVICES, msg: str, *args):
    #     self._broker.send(service, msg, *args)

    def _configure(self):
        super()._configure()
        self._broker.register("trade", self.__trade_event)
        self._broker.register("data_finish", self.__data_finish_event)
        self._broker.register("close_all_trades", self.__close_all_trades_event)
        self._broker.register("data_start", self.__data_start_event)
        self._broker.register("debug_breakpoint", self.__debug_breakpoint_event)
        self._broker.register("last_feed", self.__last_feed_event)

    # def _trigger_event(self, event):
    #     pass
    
    async def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                await self._broker.send(getattr(SERVICES, service), 'stop')
        self._broker.stop()

    def __axis_format(self, ax, title):
        ax.set_title(title)
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed')


    async def __print_charts(self,
                    custom_charts: List[CustomChart] ):
        plt.close()
        
        #plot trades chart
        # position: Position = self.positions[0]
        number_of_custom_charts = 0
        if custom_charts != None:
            number_of_custom_charts = len([ch for ch in custom_charts if not ch.display_on_price_chart])

        chartable_symbols = [sym for sym in self.data_schema.data \
                if sym.display_chart_in_summary == True]
        axs_number_used = 0

        #prepare axes
        self.__fig, axs = plt.subplots(nrows=1+ len(chartable_symbols)+number_of_custom_charts, \
                ncols=1, sharex = True, figsize=(13, 13))
        if type(axs)!= np.ndarray:
            # if only 1 axis its returned not in array
            axs = [axs]
        ax = None
        # plot instrment charts
        for sym in chartable_symbols:
            position: Position = sym.additional_properties['position']
            # if position:
            if self.__last_timestamp != None:
                main_chart = sym.additional_properties['chart_data_frame'].loc[sym.additional_properties['chart_data_frame']['timestamp'] <= \
                        self.__last_timestamp]
            ax = main_chart.plot(x ='timestamp', y='price', kind = 'line', ax=axs[axs_number_used])
            axs_number_used += 1
            self.__axis_format(ax, sym.symbol +" - "+sym.historical_data_source)
            if self.data_schema.log_scale_valuation_chart:	
                ax.yaxis.set_major_formatter(ScalarFormatter())
            if position:
                normalized_quants = self.__normalize([abs(trade[2]) for trade in position.trades], (5,15))   
                for trade, quant in zip(position.trades, normalized_quants):
                    ax.plot(trade[0], trade[1], '.g' if trade[2]>0 else '.r', ms=quant)

        if len(self.cumulated_money_chart) > 0:
            #plot money chart
            money_df = pd.DataFrame(self.cumulated_money_chart, columns=['timestamp', 'income'])
            ax = money_df.plot(x ='timestamp', y='income', kind = 'line', ax=axs[axs_number_used], sharex = ax)
            axs_number_used += 1
            
        #plot custom charts
        if custom_charts != None:
            for i, ch in enumerate(custom_charts):
                chart = [[c.timestamp, c.value] for c in ch.chart ]
                custom_df = pd.DataFrame(chart, columns=['timestamp', ch.name])
                if ch.display_on_price_chart:
                    custom_df.plot(x ='timestamp', y=ch.name, kind = 'line', ax=axs[0], \
                            sharex = ax, color = ch.color)
                else:
                    ax = custom_df.plot(x ='timestamp', y=ch.name, kind = 'line', ax=axs[axs_number_used], \
                            sharex = ax, color = ch.color)
                    axs_number_used += 1
                    self.__axis_format(ax, ch.name)
                    if ch.log_scale:
                        ax.yaxis.set_major_formatter(ScalarFormatter())
        if self.__chart_displayed == False:
            plt.ion()
            plt.show(block = False)
            self.__chart_displayed = True


    def __add_position(self, data_symbol: DataSymbol) -> Position:
        pos = Position()
        data_symbol.additional_properties['position'] = pos
        self.__update_last_instrument_prices()
        return pos


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

    async def __recalculate_positions(self):
        positions: List[Position] = [elem.additional_properties['position'] for elem in self.data_schema.data]
        positions = [pos for pos in positions if pos != None]
        for pos in positions:
            pos.position_outcome =  - pos.buy_summary_cost - pos.sell_summary_cost + \
                    pos.number_of_actions * pos.last_instrument_price
        current_capital = sum([pos.position_outcome for pos in positions])
        current_invested = sum([abs(pos.number_of_actions) * pos.last_instrument_price\
                for pos in positions])
        self.cumulated_money_chart.append([self.__last_timestamp, current_capital])
        await self._broker.send(SERVICES.python_executor, 'set_current_capital_event', current_capital)
        await self._broker.send(SERVICES.python_executor, 'set_current_invested_event', current_invested)

    def __get_data_symbol(self, symbol: str, source: str):
        arr = [sym for sym in self.data_schema.data if sym.symbol ==\
                symbol and sym.historical_data_source == source]
        if len(arr) == 0:
            raise Exception('No data symbol found')
        if len(arr) > 1: 
            raise Exception('More than one symbol found')
        return arr[0]

    async def __trade(self, trade: Trade):
        symbol: DataSymbol = self.__get_data_symbol(trade.symbol, trade.source)
        position = symbol.additional_properties['position']
        if not position:
            position = self.__add_position(symbol)
        if trade.price == 0 and trade.timestamp == 0:
            trade.price = position.last_instrument_price
            trade.timestamp = self.__last_timestamp
        if trade.price <= 0 or trade.timestamp <= 0:
            self._log('Cannot make trade with this price and timestamp:', trade.price,';', trade.timestamp)
            return
        self._log(f"Trade for [{symbol.symbol}]: time={datetime.utcfromtimestamp(trade.timestamp/1000)}, | value={trade.value}, price={trade.price}")
        position.trades.append([trade.timestamp, trade.price, trade.value])
        # print('trade price', trade.price)
        position.number_of_actions += trade.value / trade.price
        if trade.value > 0: 
            position.buy_summary_cost += trade.value
        else:
            position.sell_summary_cost += trade.value
        await self.__recalculate_positions()
        

    async def __print_summary(self, 
                custom_charts: List[CustomChart], 
                display_charts = True
                # file_names: List[str],
                # main_instrument_price: float,
                # last_timestamp: Union[int, None] = None
                ):
        self._log('==========================')
        self._log(('BREAKPOINT ' if self.__last_timestamp != None else '') + 'SUMMARY')
        finish_time = tm.time()
        time_of_backtest = finish_time - self.__backtest_start_time
        self._log('time of backtest:', round(time_of_backtest,2), '[s]')
        # self._log('number of trades:', len(self.trades))
        # self._log('buy_summary_cost:', self.buy_summary_cost)
        # self._log('sell_summary_cost:', self.sell_summary_cost)
        # self._log('number of unrealized actions:', self.number_of_actions)
        # self._log('biggest investment: ', self.biggest_investment)
        # self._log('actual price:', main_instrument_price)
        # income = - self.buy_summary_cost - self.sell_summary_cost + self.number_of_actions * main_instrument_price
        if len(self.cumulated_money_chart) > 0:
            self._log('income:', self.cumulated_money_chart[-1][1])
        self._log('==========================')
        self._log('')
        if display_charts:
            await self.__print_charts(custom_charts)

    def __load_instrument_chart(instrument):
        loaded_df = None
        
        return loaded_df

    # COMMANDS

    async def __data_finish_event(self, finish_params):
        finish_params = DataFinish(**finish_params)
        self._log('')
        self._log('====================================================')
        self._log('BACKTEST FINISHED')
        await self.__print_summary(finish_params.custom_charts)
        self._log('====================================================')
        plt.show(block = True)
        await self.__stop_all_services()

    async def __trade_event(self, msg):
        trade: Trade = Trade(**msg)
        await self.__trade(trade)

    async def __last_feed_event(self, msg):
        # print('last feed event')
        self.__last_feed = LastFeed(**msg)
        self.__last_timestamp = self.__last_feed.last_feed[0]
        self.__update_last_instrument_prices()

    def __update_last_instrument_prices(self):
        for data_symbol, last_feed in zip(self.data_schema.data, self.__last_feed.last_feed[1:]):
            # print('updating pos')

            position: Position = data_symbol.additional_properties['position']
            if position:
                # print('upda')
                # print(type(last_feed))
                if type(last_feed) == float or type(last_feed) == int: 
                    position.last_instrument_price = last_feed
                    continue 
                if type(last_feed) == list:
                    print('feed is 3d')
                    if type(last_feed[0]) == float or type(last_feed[0]) == int:
                        position.last_instrument_price = last_feed[0]
                    continue

                raise Exception('Error during setting last instrument price')

    async def __close_all_trades_event(self):
        self._log(f"Received close all trades command NOT IMPLEMENTED")

        #TODO

    async def __data_start_event(self, start_params):
        start_params = DataStart(**start_params)
        self.__backtest_start_time = start_params.start_time
        
        for element in start_params.file_names:
            dfs = []
            for file in element.files:
                df = pd.read_csv(join(self.downloaded_data_path, file.to_filename()), \
                        index_col=None, header=None, names=['timestamp', 'price'])
                dfs.append(df)
            symbol = self.__get_data_symbol(element.symbol, element.source)
            symbol.additional_properties['chart_data_frame'] = pd.concat(dfs)


    async def __debug_breakpoint_event(self, breakpoint_params):
        breakpoint_params = DebugBreakpoint(**breakpoint_params)
        await self.__print_summary(breakpoint_params.custom_charts, breakpoint_params.display_charts)


