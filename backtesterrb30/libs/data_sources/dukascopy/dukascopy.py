from datetime import datetime
from enum import Enum
from os import getcwd, remove, system, walk
from os.path import join
from shutil import rmtree
from typing import Union
from dateutil import parser


import pandas as pd

from backtesterrb30.libs.data_sources.data_source_base import DataSource
from backtesterrb30.libs.interfaces.utils.data_symbol import DataSymbol
from backtesterrb30.libs.utils.timestamps import timestamp_to_datetime
import requests

# from backtesterrb30.historical_data_feeds.modules.utils import validate_dataframe_timestamps


class DUKASCOPY_INTERVALS_2(str, Enum):
    tick: str = "tick"
    minute: str = "minute"
    minute5: str = "minute5"
    minute15: str = "minute15"
    minute30: str = "minute30"
    hour: str = "hour"
    hour4: str = "hour4"
    day: str = "day"
    month: str = "month"


def get_data_start_for_interval(
    interval: DUKASCOPY_INTERVALS_2, metadata: dict
) -> datetime:
    if interval == DUKASCOPY_INTERVALS_2.tick:
        return parser.isoparse(metadata["startHourForTicks"])
    elif interval in {
        DUKASCOPY_INTERVALS_2.minute,
        DUKASCOPY_INTERVALS_2.minute5,
        DUKASCOPY_INTERVALS_2.minute15,
        DUKASCOPY_INTERVALS_2.minute30,
    }:
        return parser.isoparse(metadata["startDayForMinuteCandles"])
    elif interval in {DUKASCOPY_INTERVALS_2.hour, DUKASCOPY_INTERVALS_2.hour4}:
        return parser.isoparse(metadata["startMonthForHourlyCandles"])
    elif interval in {DUKASCOPY_INTERVALS_2.day, DUKASCOPY_INTERVALS_2.month}:
        return parser.isoparse(metadata["startYearForDailyCandles"])
    else:
        raise ValueError(f"Unsupported interval: {interval}")


def load_metadata():
    url = "https://raw.githubusercontent.com/Leo4815162342/dukascopy-node/master/src/utils/instrument-meta-data/generated/instrument-meta-data.json"
    response = requests.get(url)
    return response.json()


class DukascopyDataSource(DataSource):
    INTERVALS = DUKASCOPY_INTERVALS_2
    NAME = "dukascopy"

    def __init__(self, logger=print):
        super().__init__(False, logger)
        self.instruments_metadata = load_metadata()

    def __get_ducascopy_interval(self, interval: str) -> str:
        if interval == "tick":
            return "tick"
        if interval == "minute":
            return "m1"
        if interval == "minute5":
            return "m5"
        if interval == "minute15":
            return "m15"
        if interval == "minute30":
            return "m30"
        if interval == "hour":
            return "h1"
        if interval == "day":
            return "d1"
        if interval == "month":
            return "mn1"

    def _get_interval_miliseconds(self, interval: str) -> Union[int, None]:
        if interval == "tick":
            return None
        if interval == "minute":
            return 60 * 1000
        if interval == "minute5":
            return 5 * 60 * 1000
        if interval == "minute15":
            return 15 * 60 * 1000
        if interval == "minute30":
            return 30 * 60 * 1000
        if interval == "hour":
            return 60 * 60 * 1000
        if interval == "day":
            return 24 * 60 * 60 * 1000
        if interval == "month":
            return None

    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        metadata = self.instruments_metadata[data.symbol]
        if metadata is None:
            self._log(
                'Error. Instrument "' + data.symbol + '" does not exists on dukascopy.'
            )
            return False
        start_date = get_data_start_for_interval(data.interval, metadata)
        if start_date > data.backtest_date_start:
            self._log("Error. First avaliable date of ", data.symbol, "is", start_date)
            return False
        return True

    async def _download_instrument_data(
        self,
        instrument: str,
        interval: str,
        time_start: int,
        time_stop: Union[int, None],
    ) -> pd.DataFrame:
        self._log("Downloading dukascopy data", instrument)
        """
        documentation: 
        https://github.com/Leo4815162342/dukascopy-node
        """

        duca_interval = self.__get_ducascopy_interval(interval)
        time_start_datetime = timestamp_to_datetime(time_start)
        if [
            time_start_datetime.hour,
            time_start_datetime.minute,
            time_start_datetime.second,
            time_start_datetime.microsecond,
        ] != [0, 0, 0, 0]:
            raise Exception(
                "Cannot dowload data with this time_start! Intervals must be in day graduality"
            )
        time_stop_datetime = timestamp_to_datetime(time_stop)
        if [
            time_stop_datetime.hour,
            time_stop_datetime.minute,
            time_stop_datetime.second,
            time_stop_datetime.microsecond,
        ] != [0, 0, 0, 0]:
            raise Exception(
                "Cannot dowload data with this time_stop! Intervals must be in day graduality"
            )
        from_param = datetime.fromtimestamp(time_start // 1000.0).strftime("%Y-%m-%d")
        to_param = datetime.fromtimestamp(time_stop // 1000.0).strftime("%Y-%m-%d")
        if from_param == to_param:
            raise Exception("The same start and stop date")
        here = getcwd()
        cache_path = join(here, "cache_dukascopy")
        try:
            rmtree(cache_path)
        except Exception:
            pass
        string_params = [
            " -i " + instrument,
            " -from " + from_param,
            " -to " + to_param,
            " -s",
            " -t " + duca_interval,
            " -fl",
            " -f csv",
            " -dir " + cache_path,
            " -p bid",
        ]
        command = "npx --yes dukascopy-node"
        for param in string_params:
            command += param
        result = system(command)
        if result != 0:
            self._log("Node is not installed?")
            raise Exception("Command not found or failed to execute: " + command)
        name_of_created_file = next(walk(cache_path), (None, None, []))[2][0]
        df = pd.read_csv(
            join(cache_path, name_of_created_file), index_col=None, header=None
        )
        if duca_interval == "tick":
            df = df.iloc[1:, [0, 2]]
        else:
            df = df.iloc[1:, [0, 1]]
        if name_of_created_file and name_of_created_file != "":
            remove(join(cache_path, name_of_created_file))
        # print('Dukascopy df shape after dl', df.shape)
        # print('head', str(df.head(1)))
        # print('tail', str(df.tail(1)))
        return df
