import pandas as pd
import numpy as np
import joblib

from libs.necessery_imports.model_imports import *
from random import randint
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
        self._set_buffer_length(49)
        self.csv = pd.DataFrame([], columns=self.columns)
        self.model = load_model('models/test_model.h5')
        self.scaler = joblib.load('models/scaler.gz')

    #override
    def on_feed(self, data: list):
        if self.counter % 300 == 0:
            df = pd.DataFrame(np.array(data).T, columns=self.columns)
            df[df.columns[1:]] = df[df.columns[1:]].diff()
            df.dropna(inplace=True)
            pred = self.model.predict(np.array([self.scaler.transform(df)]), verbose=0)
            if abs(pred.sum()) > 1:
                quant = int(pred.sum())
                if quant != 0:
                    message = {
                        'value': quant,
                        'trade_timestamp': data[0][-1]
                    }
                    self._trigger_event(message)
        #self.csv.loc[len(self.csv)] = np.array(data)[:, -1]

        #     # self._log('feed received', self.counter)
        #     # print('')
        #     # print('')
        #     # self._log('newwwwwwwwwwwwww data element')
        #     # for d in data:
        #     #     print('len d', len(d))
        #     #     print(d)
        #
        #     quant = randint(-4,4)
        #     if quant != 0:
        #         message = {
        #             'value': quant,
        #             'trade_timestamp': data[0][-1]
        #         }
        #         self._trigger_event(message)
        #     # for d in data:
        #     #     print(d)
    
        # 
        self.counter += 1

    # def on_data_finish(self):
    #     self.csv.to_csv('data/test_data.csv')



