import pandas as pd
import numpy as np
import joblib
from libs.interfaces.python_engine.custom_chart_element import CustomChartElement
from typing import List
from libs.utils.model_imports import *
from random import randint
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import tensorflow as tf
from tensorflow.keras.models import load_model
# configure model =====================================
gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
  tf.config.experimental.set_memory_growth(gpu, True)


class Model(Engine):
    
    def __init__(self, config):
        super().__init__(config)
        self.counter = 0
        self._set_buffer_length(59)
        self.csv = pd.DataFrame([], columns=self._get_columns())
        self.model = load_model('strategies/'+self.config.strategy_name+'/models/test_model.h5')
        self.scaler = joblib.load('strategies/'+self.config.strategy_name+'/models/scaler.gz')
        self.reloading_module = self._add_reloading_module('strategies.'+self.config.strategy_name+'.reloading_module.reloading_methods')

        self.actual_state = 0
        self.first_trade = True

        self.custom_chart1: List[CustomChartElement]= []
        self.custom_chart2: List[CustomChartElement]= []
        self._add_custom_chart(chart=self.custom_chart1, name='custom1', display_on_price_chart=False, log_scale=True, color='red')
        self._add_custom_chart(chart=self.custom_chart2, name='custom2', display_on_price_chart=True)


    #override
    # async def on_feed(self, data: list):
    #     if self.counter % 30 == 0:
    #         transposed = np.array(data).T
    #         # cut frame to 49/8 size but leave some space (10 frames) for closing trades.
    #         cut_frame = transposed[:-10]
    #         df = pd.DataFrame(cut_frame, columns=self._get_columns())
    #         df[df.columns[1:]] = df[df.columns[1:]].diff()
    #         df.dropna(inplace=True)
    #         pred = self.model.predict(np.array([self.scaler.transform(df)]), verbose=0)
    #         if abs(pred.sum()) > 2:
    #             quant = int(pred.sum())
    #             quant = - quant
    #             # quant = 5
    #             if quant != 0:
    #                 if True if self.actual_state> 0 else False != True if quant> 0 else False:

    #                     if self.actual_state != 0:
    #                         message = {
    #                             'value': -self.actual_state,
    #                             'price': data[self._get_main_intrument_number()][-11],
    #                             'timestamp': data[0][-11] 
    #                         }
    #                         self.actual_state = 0
    #                         self._trigger_event(message)

    #                     # open trade
    #                     self.actual_state = quant
    #                     message = {
    #                         'value': quant,
    #                         'price': data[self._get_main_intrument_number()][-11],
    #                         'timestamp': data[0][-11] 
    #                     }
    #                     self._trigger_event(message)

    #     self.counter += 1



    async def on_feed(self, data: list):
        if self.counter % 10 == 0:
            transposed = np.array(data).T
            # cut frame to 49/8 size but leave some space (10 frames) for closing trades.
            cut_frame = transposed[:-10]
            df = pd.DataFrame(cut_frame, columns=self._get_columns())
            df[df.columns[1:]] = df[df.columns[1:]].diff()
            df.dropna(inplace=True)
            pred = self.model.predict(np.array([self.scaler.transform(df)]), verbose=0)
            if abs(pred.sum()) > 2:
                quant = int(pred.sum())
                # quant = 5
                if quant != 0:
                    await self._debug_breakpoint()
                    # open trade
                    message = {
                        'value': quant,
                        'price': data[self._get_main_intrument_number()][-11],
                        'timestamp': data[0][-11] 
                    }
                    self._trigger_event(message)

                    # close trade after some time
                    message = {
                        'value': -quant,
                        'price': data[self._get_main_intrument_number()][-1],
                        'timestamp': data[0][-1] 
                    }
                    
                    #append to custom chart some staff
                    chart_obj = {
                        'timestamp': data[0][-1],
                        'value': self.counter * self.counter *0.001
                    }
                    self.custom_chart1.append(CustomChartElement(**chart_obj))
                    chart_obj = {
                        'timestamp': data[0][-1],
                        'value': data[self._get_main_intrument_number()][-11] + 100
                    }
                    self.custom_chart2.append(CustomChartElement(**chart_obj))
                    self.reloading_module.on_feed_reload(data)
                    self._trigger_event(message)
                    
        self.counter += 1

    def on_data_finish(self):
        pass


