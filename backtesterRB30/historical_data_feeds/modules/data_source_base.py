from abc import abstractmethod
from typing import Union, List
from backtesterRB30.libs.interfaces.historical_data_feeds.instrument_file import InstrumentFile
from backtesterRB30.libs.interfaces.utils.data_symbol import DataSymbol
import asyncio
import pandas as pd
from enum import Enum
from os.path import join, isfile
from os import listdir


from backtesterRB30.libs.utils.timestamps import timestamp_to_datetime

class UnregularIntervalMiliseconds(Enum):
    smaller_than_minute = 'tick'
    bigger_than_day = 'week'


class DataSource():

    def __init__(self, allow_synchronous_download: bool, logger=print):
        self._allow_synchronous_download = allow_synchronous_download
        self._log = logger

    def _raise_error(self, error_message):
        raise Exception(error_message)

    def __validate_dataframe(self, 
                        df: pd.DataFrame,
                        expected_first_data_timestamp: int,
                        expected_last_data_timestamp: int,
                        expected_data_length: int) -> bool:
        if int(df.head(1)[0]) != expected_first_data_timestamp: return False
        if int(df.tail(1)[0]) != expected_last_data_timestamp: return False
        if len(df) != expected_data_length: return False
        return True

    async def download_instrument(self,
                        downloaded_data_path: str, 
                        instrument_file: InstrumentFile): 
        await asyncio.sleep(0.1)
        dfs: List[pd.DataFrame] = []
        df: pd.DataFrame = await self._download_instrument_data(downloaded_data_path, instrument_file)
        interval_milisedonds = self._get_interval_miliseconds(instrument_file.interval)

        if type(interval_milisedonds) != int and type(interval_milisedonds) != UnregularIntervalMiliseconds:
            self._log('Error, bad returned type of interval miliseconds')
            return

        if type(interval_milisedonds) == UnregularIntervalMiliseconds and \
                interval_milisedonds == UnregularIntervalMiliseconds.smaller_than_minute:
            dfs = df.groupby(df['timestamp'].map(lambda x: timestamp_to_datetime(x).day))
        if type(interval_milisedonds) == UnregularIntervalMiliseconds and \
                interval_milisedonds == UnregularIntervalMiliseconds.bigger_than_day:
            dfs = df.groupby(df['timestamp'].map(lambda x: timestamp_to_datetime(x).year))
        if type(interval_milisedonds) == int and interval_milisedonds < 1000*60: 
            dfs = df.groupby(df['timestamp'].map(lambda x: timestamp_to_datetime(x).day))
        if type(interval_milisedonds) == int and 1000*60 <= interval_milisedonds <= 1000*60*60: 
            dfs = df.groupby(df['timestamp'].map(lambda x: timestamp_to_datetime(x).month))
        if type(interval_milisedonds) == int and 1000*60*60 < interval_milisedonds: 
            dfs = df.groupby(df['timestamp'].map(lambda x: timestamp_to_datetime(x).year))
    
        for d in dfs: 
            d.to_csv(join(downloaded_data_path, instrument_file.to_filename()), 
                index=False, header=False)
        
    def load_instrument_file(self, instrument_file: InstrumentFile):
        pass

    def get_files_to_download(self, data_symbol: DataSymbol):
        files: List[InstrumentFile] = self.__get_instrument_files(data_symbol)
        # self._log('files to download "'+str(data_symbol.symbol)+'" :', files)
        files_in_directory = [f for f in listdir(self.downloaded_data_path) if isfile(join(self.downloaded_data_path, f))]
        files_to_download = list(set([f.to_filename() for f in files]) - set(files_in_directory))
        files_to_download: List[InstrumentFile] = [InstrumentFile.from_filename(file) for file in files_to_download]

    
    def __get_instrument_files(self, data_symbol: DataSymbol):
        interval_milisedonds = self._get_interval_miliseconds(data_symbol.interval.value)
        if type(interval_milisedonds) != int and type(interval_milisedonds) != UnregularIntervalMiliseconds:
            self._log('Error, bad returned type of interval miliseconds')
            return
        if type(interval_milisedonds) == int and interval_milisedonds < 1000*60 or \
                (type(interval_milisedonds) == UnregularIntervalMiliseconds and \
                interval_milisedonds == UnregularIntervalMiliseconds.smaller_than_minute): 

            pass
        if type(interval_milisedonds) == int and 1000*60 <= interval_milisedonds <= 1000*60*60: 

            pass
        if type(interval_milisedonds) == int and 1000*60*60 < interval_milisedonds or \
                (type(interval_milisedonds) == UnregularIntervalMiliseconds and \
                interval_milisedonds == UnregularIntervalMiliseconds.bigger_than_day):
                 
            pass

    async def validate_instrument(self, data: DataSymbol) -> bool:
        await asyncio.sleep(0.1)
        return await self._validate_instrument_data(data)

    @abstractmethod
    def _get_interval_miliseconds(self, interval: str) -> Union[int, UnregularIntervalMiliseconds]: 
        pass

    @abstractmethod
    async def _validate_instrument_data(self, data: DataSymbol) -> bool:
        pass
    
    @abstractmethod
    async def _download_instrument_data(self,
                        downloaded_data_path: str, 
                        instrument_file: InstrumentFile) -> pd.DataFrame:
        """
        First downloaded timestamp should exactly exuals instrument_file.time_start (can be bigger if u are downloading ticks)
        Last downloaded timestamp should exactly exuals one interval before instrument_file.time_stop ()
        """
        pass