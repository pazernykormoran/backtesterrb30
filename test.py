
# # Contrived example of generating a module named as a string
# full_module_name = "serve"

# # The file gets executed upon import, as expected.
# mymodule = importlib.import_module(full_module_name)

# # # Then you can use the module like normal
# # base1_obj = mymodule.Base1()
# # base1_obj.base1_func1()

# class Klasa2(mymodule.Base1):
#     def __init__(self):
#         super()

#     def klasa2_func1(self):
#         print('klasa2_func1')
#         self.base1_func1()

# klasa2_obj = Klasa2()
# klasa2_obj.klasa2_func1()

# import os
# os.system('npm install dukascopy-node --save')

# os.system('npx dukascopy-node -i btcusd -from 2018-01-01 -to 2019-01-14 -t d1 -f csv -s')
# os.system('npx dukascopy-node -i btcusd -from 2018-01-20 -to 2019-01-30 -t d1 -f csv -s')

# ===========================================
# # # # # binance avaliable instruments
# from datetime import datetime
# from binance.client import Client
# from os import getenv
# from dotenv import load_dotenv
# load_dotenv()

# api_secret=getenv("binance_api_secret")
# api_key=getenv("binance_api_key")
# client = Client(api_key, api_secret)
# exchange_info = client.get_exchange_info()
# klines = client.get_historical_klines('BTCUSDT', 
#         Client.KLINE_INTERVAL_1MONTH, 1609718400000, 1638921600000)
# for kl in klines:
#     print(datetime.utcfromtimestamp(kl[0]/1000))
# for s in exchange_info['symbols']:
#     print(s['symbol'])
# ===========================================

# import matplotlib.pyplot as plt
# import numpy as np

# x = np.linspace(0, 6*np.pi, 100)
# y = np.sin(x)

# # You probably won't need this if you're embedding things in a tkinter plot...
# plt.ion()

# fig = plt.figure()
# ax = fig.add_subplot(111)
# line1, = ax.plot(x, y, 'r-') # Returns a tuple of line objects, thus the comma

# for phase in np.linspace(0, 10*np.pi, 500):
#     line1.set_ydata(np.sin(x + phase))
#     fig.canvas.draw()
#     fig.canvas.flush_events()

#====================================================
# from xnt.http_api import HTTPApi, current_api, AuthMethods
# from os import getenv
# from dotenv import load_dotenv
# load_dotenv()
# import json

# exante_app_id=getenv("exante_app_id")
# exante_access_key=getenv("exante_access_key")

# client = HTTPApi(AuthMethods.BASIC, appid=exante_app_id, acckey=exante_access_key)

# accs = client.get_user_accounts('3.0')
# print(accs)
# abc = client.get_currencies('3.0')
# print(abc)
# print('')
# # symbols = client.get_symbols()
# # print(symbols)
# exchanges = client.get_exchanges()
# print('exchanges')
# print(exchanges)

# instrument_by_type = client.get_symbols_by_exch('NASDAQ')
# print('instrument_by_type downloaded')
# print('jsoning.')

# from datetime import datetime, timezone
# d = datetime.now()
# d= d.replace(tzinfo=timezone.utc)
# print(d.tzinfo is not None and d.tzinfo.utcoffset(d) is not None)

# import time
# t = time.time()
# print('')
# print(t*1000)

# class Asd():
    
#     def __init__(self):
#         pass

#     def set_com_broker(self, com_broker):
#         self.com_broker = com_broker

#     def service_call(self):
#         print('service call')
#         self.com_broker.broker_call()


# class Broker():
#     def __init__(self, service):
#         self.service = service

#     def broker_call(self):
#         print('broker call')
#         self.service.service_call()

# asd = Asd()

# broker = Broker(asd)

# asd.set_com_broker(broker)

# asd.service_call()
# =========================================
# from importlib.machinery import SourceFileLoader

# foo = SourceFileLoader("module.name", "/home/george/workspace/project/Retire-Before-30/Engine-RB30/test2.py").load_module()
# foo.asd()
# ============================================
