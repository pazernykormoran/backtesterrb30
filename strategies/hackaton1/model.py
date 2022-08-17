import pandas as pd
import numpy as np
import joblib

from libs.necessery_imports.model_imports import *
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

    #override
    def on_feed(self, data: list):
        if self.counter % 5 == 0:
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
                    self._trigger_event(message)
        self.counter += 1

    # def on_data_finish(self):
    #     self.csv.to_csv('data/test_data.csv')



