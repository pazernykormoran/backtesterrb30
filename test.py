# import importlib

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
# from binance.client import Client
# from os import getenv
# from dotenv import load_dotenv
# load_dotenv()

# api_secret=getenv("binance_api_secret")
# api_key=getenv("binance_api_key")
# client = Client(api_key, api_secret)
# exchange_info = client.get_exchange_info()
# for s in exchange_info['symbols']:
#     print(s['symbol'])
# ===========================================

import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 6*np.pi, 100)
y = np.sin(x)

# You probably won't need this if you're embedding things in a tkinter plot...
plt.ion()

fig = plt.figure()
ax = fig.add_subplot(111)
line1, = ax.plot(x, y, 'r-') # Returns a tuple of line objects, thus the comma

for phase in np.linspace(0, 10*np.pi, 500):
    line1.set_ydata(np.sin(x + phase))
    fig.canvas.draw()
    fig.canvas.flush_events()