from binance.client import Client
from os import getenv

api_secret=getenv("binance_api_secret")
api_key=getenv("binance_api_key")
client = Client(api_key, api_secret)
exchange_info = client.get_exchange_info()
for s in exchange_info['symbols']:
    print(s['symbol'])