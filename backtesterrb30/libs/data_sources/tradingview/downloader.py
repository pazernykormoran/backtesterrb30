import datetime
import enum
import json
import logging
import random
import re
import string
import pandas as pd
from websocket import create_connection
import requests
import asyncio

logger = logging.getLogger(__name__)


class Interval(enum.Enum):
    in_1_minute = "1"
    in_3_minute = "3"
    in_5_minute = "5"
    in_15_minute = "15"
    in_30_minute = "30"
    in_45_minute = "45"
    in_1_hour = "1H"
    in_2_hour = "2H"
    in_3_hour = "3H"
    in_4_hour = "4H"
    in_daily = "1D"
    in_weekly = "1W"
    in_monthly = "1M"


class TradingviewDownloader:
    sign_in_url = 'https://www.tradingview.com/accounts/signin/'
    ws_headers = json.dumps({"Origin": "https://data.tradingview.com"})
    signin_headers = {'Referer': 'https://www.tradingview.com'}
    ws_timeout = 5

    def __init__(
        self,
        username: str = None,
        password: str = None,
    ) -> None:
        """Create TvDatafeed object

        Args:
            username (str, optional): tradingview username. Defaults to None.
            password (str, optional): tradingview password. Defaults to None.
        """

        self.ws_debug = False

        self.token = self.auth(username, password)

        if self.token is None:
            self.token = "unauthorized_user_token"
            logger.warning(
                "you are using nologin method, data you access may be limited"
            )

        self.ws = None
        self.session = self.generate_session()
        self.chart_session = self.generate_chart_session()

    def auth(self, username, password):

        if (username is None or password is None):
            token = None

        else:
            data = {"username": username,
                    "password": password,
                    "remember": "on"}
            try:
                response = requests.post(
                    url=self.sign_in_url, data=data, headers=self.signin_headers)
                token = response.json()['user']['auth_token']
            except Exception as e:
                logger.error('error while signin')
                token = None

        return token

    def create_connection(self):
        logging.debug("creating websocket connection")
        self.ws = create_connection(
            "wss://data.tradingview.com/socket.io/websocket", headers=self.ws_headers, timeout=self.ws_timeout
        )

    @staticmethod
    def filter_raw_message(text):
        try:
            found = re.search('"m":"(.+?)",', text).group(1)
            found2 = re.search('"p":(.+?"}"])}', text).group(1)

            return found, found2
        except AttributeError:
            logger.error("error in filter_raw_message")

    @staticmethod
    def generate_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters)
                                for i in range(stringLength))
        return "qs_" + random_string

    @staticmethod
    def generate_chart_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters)
                                for i in range(stringLength))
        return "cs_" + random_string

    @staticmethod
    def prepend_header(st):
        return "~m~" + str(len(st)) + "~m~" + st

    @staticmethod
    def construct_message(func, param_list):
        return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))

    def create_message(self, func, paramList):
        return self.prepend_header(self.construct_message(func, paramList))

    def send_message(self, func, args):
        m = self.create_message(func, args)
        if self.ws_debug:
            print(m)
        self.ws.send(m)

    @staticmethod
    def create_df(raw_data, symbol):
        try:
            out = re.search('"s":\[(.+?)\}\]', raw_data).group(1)
            x = out.split(',{"')
            data = []
            volume_data = True

            for xi in x:
                xi = re.split("\[|:|,|\]", xi)
                ts = int(float(xi[4])*1000)

                row = [ts]

                for i in range(5, 10):

                    # skip converting volume data if does not exists
                    if not volume_data and i == 9:
                        row.append(0.0)
                        continue
                    try:
                        row.append(float(xi[i]))

                    except ValueError:
                        volume_data = False
                        row.append(0.0)
                        logger.debug('no volume data')

                data.append(row)

            data = pd.DataFrame(
                data, columns=["timestamp", "open",
                               "high", "low", "close", "volume"]
            )
            data.insert(0, "symbol", value=symbol)
            return data
        except AttributeError:
            logger.error("no data, please check the exchange and symbol")
            return pd.DataFrame()

    @staticmethod
    def format_symbol(symbol, exchange, contract: int = None):

        if ":" in symbol:
            pass
        elif contract is None:
            symbol = f"{exchange}:{symbol}"

        elif isinstance(contract, int):
            symbol = f"{exchange}:{symbol}{contract}!"

        else:
            raise ValueError("not a valid contract")

        return symbol

    async def get_hist(
        self,
        symbol: str,
        from_timestamp: int,
        exchange: str = "NSE",
        interval: Interval = Interval.in_daily,
        fut_contract: int = None,
        extended_session: bool = False,
    ) -> pd.DataFrame:
        """get historical data

        Args:
            symbol (str): symbol name
            exchange (str, optional): exchange, not required if symbol is in format EXCHANGE:SYMBOL. Defaults to None.
            interval (str, optional): chart interval. Defaults to 'D'.
            n_bars (int, optional): no of bars to download, max 5000. Defaults to 10.
            fut_contract (int, optional): None for cash, 1 for continuous current contract in front, 2 for continuous next contract in front . Defaults to None.
            extended_session (bool, optional): regular session if False, extended session if True, Defaults to False.

        Returns:
            pd.Dataframe: dataframe with sohlcv as columns
        """
        symbol = self.format_symbol(
            symbol=symbol, exchange=exchange, contract=fut_contract
        )

        interval = interval.value

        self.create_connection()

        self.send_message("set_auth_token", [self.token])
        self.send_message("chart_create_session", [self.chart_session, ""])
        self.send_message("quote_create_session", [self.session])
        self.send_message(
            "quote_set_fields",
            [
                self.session,
                "ch",
                "chp",
                "current_session",
                "description",
                "local_description",
                "language",
                "exchange",
                "fractional",
                "is_tradable",
                "lp",
                "lp_time",
                "minmov",
                "minmove2",
                "original_name",
                "pricescale",
                "pro_name",
                "short_name",
                "type",
                "update_mode",
                "volume",
                "currency_code",
                "rchp",
                "rtc",
            ],
        )

        # print(self.session)

        self.send_message(
            "quote_add_symbols", [self.session, symbol,
                                  {"flags": ["force_permission"]}]
        )
        self.send_message("quote_fast_symbols", [self.session, symbol])

        self.send_message(
            "resolve_symbol",
            [
                self.chart_session,
                "symbol_1",
                '={"symbol":"'
                + symbol
                + '","adjustment":"splits","session":'
                + ('"regular"' if not extended_session else '"extended"')
                + "}",
            ],
        )
        self.send_message(
            "create_series",
            [self.chart_session, "sds_1", "s1", "symbol_1", interval, 1000],
        )
        self.send_message("switch_timezone", [
                            self.chart_session, "exchange"])

        raw_data = ""

        logger.debug(f"getting data for {symbol}...")
        while True:
            try:
                result = self.ws.recv()
                raw_data = raw_data + result + "\n"
            except Exception as e:
                logger.error(e)
                break

            if "series_completed" in result:
                break

        df = self.create_df(raw_data, symbol)

        list_dfs = []
        list_dfs.append(df)
        encountered_part_frames_number = 0
        encountered_zero_frames_number = 0
        while True:

            self.send_message(
                "request_more_data",
                [self.chart_session, "sds_1", 1000],
            )
            # result = tv.ws.recv()
            raw_data2 = ""
            while True:
                try:
                    result = self.ws.recv()
                    # print(result)
                    raw_data2 = raw_data2 + result + "\n"
                except Exception as e:
                    logger.error(e)
                    break

                if "series_completed" in result:
                    # print('completed 2')

                    break
                
                if result == '':
                    break
            from random import randint
            # time.sleep(randint(1,3))

            df = self.create_df(raw_data2, symbol)
            if len(df)> 0:
                list_dfs.append(df)
            # print('len df', len(df))
            if len(df) < 0 and len(df) < 1000:
                if encountered_part_frames_number == 1:
                    print('second part freame. sleepin 20 s')
                    asyncio.sleep(20)
                encountered_part_frames_number +=1
            if len(df) == 0:
                if encountered_zero_frames_number == 1:
                    raise Exception('Tradingview data out of range.'+str(symbol)+'\
                         '+str(exchange)+ ' ' +str(fut_contract)+' Last avaliable date for interval '+str(interval+' is ' 
                        + str(datetime.datetime.utcfromtimestamp(list_dfs[-1].iloc[-1,1]/1000))))
                encountered_zero_frames_number +=1

            if len(df) > 0:
                print(df.iloc[-1,1])
                if df.iloc[-1,1] <= from_timestamp:
                    # print('smaller')
                    break
                
        # print(list_dfs)
        # reversed = list_dfs.reverse()
        # print(reversed)
        return pd.concat(list_dfs[::-1])

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG)
#     tv = TvDatafeed(
#     )
#     print(tv.get_hist("CRUDEOIL", "MCX", fut_contract=1))
#     # print(tv.get_hist("NIFTY", "NSE", fut_contract=1))
#     # print(
#     #     tv.get_hist(
#     #         "EICHERMOT",
#     #         "NSE",
#     #         interval=Interval.in_1_hour,
#     #         n_bars=500,
#     #         extended_session=False,
#     #     )
#     # )
