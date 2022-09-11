import pandas as pd
import numpy as np
import joblib

from libs.necessery_imports.model_imports import *
from random import randint
import os
import pandas_ta as pta
import matplotlib.pyplot as plt
import time

class Model(Engine):
    def __init__(self, config):
        super().__init__(config)
        self.counter = 0
        self._set_buffer_length(59)
        self.actual_state = 0
        self.first_trade = True

        self.rsi_arr = []

    async def on_feed(self, buffor: list):
        df = pd.DataFrame(np.array(buffor).T, columns=self._get_columns())
        col = self._get_columns()[-1]
        ema_8 = df[col].ewm(span=8).mean().values[-1]
        ema_13 = df[col].ewm(span=13).mean().values[-1]
        ema_21 = df[col].ewm(span=21).mean().values[-1]
        ema_55 = df[col].ewm(span=55).mean().values[-1]
        # time.sleep(0.1)
        rsi = pta.rsi(df[col], length=14).values[-1]
        self.rsi_arr.append(rsi)
        # print('===============')
        # print(rsi)
        

        if ema_8 > ema_13 and ema_8 > ema_21 and ema_8 > ema_55:
            # print('above')
            if self.actual_state == -5 or self.first_trade:
                self.first_trade = False
                message = {
                    'value': -self.actual_state,
                }
                self.actual_state = 0
                self._trigger_event(message)

            if rsi >70 and  self.actual_state == 0:
                # print('RSIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII')
                message = {
                    'value': 5,
                }
                self.actual_state += 5
                self._trigger_event(message)

        elif ema_8 < ema_13 and ema_8 < ema_21 and ema_8 < ema_55:
            # print('under')

            if self.actual_state == 5 or self.first_trade:
                self.first_trade = False
                message = {
                    'value': -self.actual_state,
                }
                self.actual_state = 0
                self._trigger_event(message)

            if rsi <30 and  self.actual_state == 0:
                # print('RSIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII')
                message = {
                    'value': -5,
                }
                self.actual_state -= 5
                self._trigger_event(message)


    def on_data_finish(self):
        # plt.figure()
        # df = pd.DataFrame(self.rsi_arr)
        # df.plot()
        # plt.show(block=True)
        pass
