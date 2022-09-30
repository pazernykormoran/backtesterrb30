
import asyncio
from backtesterRB30.libs.interfaces.python_backtester.data_start import DataStart
from backtesterRB30.libs.interfaces.python_backtester.debug_breakpoint import DebugBreakpoint
from backtesterRB30.libs.interfaces.python_backtester.last_feed import LastFeed
from backtesterRB30.libs.interfaces.python_backtester.positions import Position
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
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
from matplotlib.ticker import ScalarFormatter
import time as tm
import numpy as np
from typing import List, Union
from datetime import datetime

class Backtester(ZMQ):
    
    downloaded_data_path = '/var/opt/data_historical_downloaded'

    def __init__(self, config: dict, logger=print):
        super().__init__(config, logger)
        self.data_schema: DataSchema = import_data_schema(self.config.strategy_path)
        
        self.trading_instruments_charts = []
        self.cumulated_money_chart = []
        self.positions: List[Position] = []
        self.__last_feed: LastFeed = {}
        self.__last_timestamp: int = 0
        self.__actual_money_invested = 0
        # self.trades = []

        # self.number_of_actions = 0
        # self.buy_summary_cost = 0
        # self.sell_summary_cost = 0
        # self.biggest_investment = 0
        # self.__file_names = []
        self.__backtest_start_time = 0
        self.__fig = None
        self.__chart_displayed = False

        super()._register("trade", self.__trade_event)
        super()._register("data_finish", self.__data_finish_event)
        super()._register("close_all_trades", self.__close_all_trades_event)
        super()._register("data_start", self.__data_start_event)
        super()._register("debug_breakpoint", self.__debug_breakpoint_event)
        super()._register("last_feed", self.__last_feed_event)

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
    
    def _trigger_event(self, event):
        pass
    
    async def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                super()._send(getattr(SERVICES, service), 'stop')
        super()._stop()

    def axis_format(self, ax, title):
        ax.set_title(title)
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed')

    async def __print_charts(self,
                    custom_charts: List[CustomChart] ):
        plt.close()
        if len(self.cumulated_money_chart) > 0:
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
            # plot instrment charts
            for sym in chartable_symbols:
                position = self.__get_position(sym)
                if position:
                    main_chart = position.instrument_chart
                    # print(position.instrument_chart)
                    if self.__last_timestamp != None:
                        main_chart = position.instrument_chart.loc[position.instrument_chart['timestamp'] <= \
                                self.__last_timestamp]
                    ax = main_chart.plot(x ='timestamp', y='price', kind = 'line', ax=axs[axs_number_used])
                    axs_number_used += 1
                    self.axis_format(ax, sym.symbol +" - "+sym.historical_data_source.value)
                    if self.data_schema.log_scale_valuation_chart:	
                        ax.yaxis.set_major_formatter(ScalarFormatter())
                    normalized_quants = self.__normalize([abs(trade[2]) for trade in position.trades], (5,15))   
                    for trade, quant in zip(position.trades, normalized_quants):
                        ax.plot(trade[0], trade[1], '.g' if trade[2]>0 else '.r', ms=quant)
                else:
                    instrument_chart = self.__get_instrument_chart(sym)
                    main_chart = instrument_chart
                    if self.__last_timestamp != None:
                        main_chart = instrument_chart.loc[instrument_chart['timestamp'] <= self.__last_timestamp]
                    ax = main_chart.plot(x ='timestamp', y='price', kind = 'line', ax=axs[axs_number_used])
                    self.axis_format(ax, sym.symbol +" - "+sym.historical_data_source.value)
                    axs_number_used += 1
                    if self.data_schema.log_scale_valuation_chart:	
                        ax.yaxis.set_major_formatter(ScalarFormatter())
                
            
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
                        self.axis_format(ax, ch.name)
                        if ch.log_scale:
                            ax.yaxis.set_major_formatter(ScalarFormatter())
            if self.__chart_displayed == False:
                plt.ion()
                plt.show(block = False)
                self.__chart_displayed = True

    def __get_instrument_chart(self, data_symbol: DataSymbol):
        filtered = [chart['data_frame'] for chart in self.trading_instruments_charts \
                if chart['symbol'] == data_symbol.symbol and chart['source'] == \
                        data_symbol.historical_data_source.value]
        if len(filtered) == 0: raise Exception('No registered instrument chart for this data_symbol')
        return filtered[0]

    def __add_position(self, data_symbol: DataSymbol) -> Position:
        print('add position')
        instrument_chart = self.__get_instrument_chart(data_symbol)
        position = {
            'data_symbol': data_symbol,
            'instrument_chart': instrument_chart
        }
        pos = Position(**position)
        self.positions.append(pos)
        self.__update_last_instrument_prices()
        return pos

    def __get_position(self, data_symbol: DataSymbol) -> Position:
        pos_founds = [pos for pos in self.positions if 
                pos.data_symbol.symbol == data_symbol.symbol and 
                pos.data_symbol.historical_data_source.value == \
                        data_symbol.historical_data_source.value]
        if len(pos_founds) == 1:
            return pos_founds[0]
        if len(pos_founds) == 0:
            return None
            

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

    def __recalculate_positions(self):
        for pos in self.positions:
            pos.position_outcome =  - pos.buy_summary_cost - pos.sell_summary_cost + \
                    pos.number_of_actions * pos.last_instrument_price
        current_capital = sum([pos.position_outcome for pos in self.positions])
        current_invested = sum([abs(pos.number_of_actions) * pos.last_instrument_price\
                for pos in self.positions])
        self.cumulated_money_chart.append([self.__last_timestamp, current_capital])
        super()._send(SERVICES.python_executor, 'set_current_capital_event', current_capital)
        super()._send(SERVICES.python_executor, 'set_current_invested_event', current_invested)

    def __trade(self, trade: Trade):
        position = self.__get_position(trade.data_symbol)
        if not position:
            position = self.__add_position(trade.data_symbol)
        if trade.price == 0 and trade.timestamp == 0:
            trade.price = position.last_instrument_price
            trade.timestamp = self.__last_timestamp
        # print(position)
        self._log(f"Trade for [{trade.data_symbol.symbol}]: time={datetime.utcfromtimestamp(trade.timestamp/1000)}, | value={trade.value}, price={trade.price}")
        position.trades.append([trade.timestamp, trade.price, trade.value])
        # print('trade price', trade.price)
        position.number_of_actions += trade.value / trade.price
        if trade.value > 0: 
            position.buy_summary_cost += trade.value
        else:
            position.sell_summary_cost += trade.value
        self.__recalculate_positions()
        # position.position_income =  - position.buy_summary_cost - position.sell_summary_cost + position.number_of_actions * position.last_instrument_price
        # if abs(trade.price* position.number_of_actions) > self.biggest_investment:
        #     self.biggest_investment = abs(trade.price* position.number_of_actions)
        # print('lodal income', local_income)
        # super()._send(SERVICES.python_executor, 'set_number_of_actions', position.number_of_actions)
        


    async def __print_summary(self, 
                custom_charts: List[CustomChart], 
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
        self._log('income:', self.cumulated_money_chart[-1][1])
        self._log('==========================')
        self._log('')
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
        self.__trade(trade)

    async def __last_feed_event(self, msg):
        print('last feed event')
        self.__last_feed = LastFeed(**msg)
        self.__last_timestamp = self.__last_feed.last_feed[0]
        self.__update_last_instrument_prices()

    def __update_last_instrument_prices(self):
        for data_symbol, last_feed in zip(self.data_schema.data, self.__last_feed.last_feed[1:]):
            # print('updating pos')

            position =self.__get_position(data_symbol)
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
        self._log(f"Received close all trades command")
        # msg = CloseAllTrades(**msg)
        # msg = dict(msg)
        # msg["quantity"] = -self.number_of_actions
        # trade: Trade = Trade(**msg)
        # self.__trade(trade)
        #TODO

    async def __data_start_event(self, start_params):
        start_params = DataStart(**start_params)
        self.__file_names = start_params.file_names
        self.__backtest_start_time = start_params.start_time
        
        for element in start_params.file_names:
            dfs = []
            for file in element.files:
                df = pd.read_csv(join(self.downloaded_data_path, file.to_filename()), \
                        index_col=None, header=None, names=['timestamp', 'price'])
                dfs.append(df)
            self.trading_instruments_charts.append({
                'symbol': element.symbol,
                'source': element.source,
                'data_frame': pd.concat(dfs)
            })
        # main_instrument_name = [element.symbol for element in self.data_schema.data if element.main == True][0]
        # files = [f for f in self.__file_names if main_instrument_name in f]
        # dfs = []
        # for file in files:
        #     df = pd.read_csv(join(self.downloaded_data_path, file), index_col=None, header=None, names=['timestamp', 'price'])
        #     dfs.append(df)
        # self.main_instrument_chart = self.trading_instruments_charts[1]['data_frame']
        

    async def __debug_breakpoint_event(self, breakpoint_params):
        breakpoint_params = DebugBreakpoint(**breakpoint_params)
        await self.__print_summary(breakpoint_params.custom_charts)


