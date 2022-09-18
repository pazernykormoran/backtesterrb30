from datetime import datetime
from json import load
from os import system, remove, walk
from os.path import join
import shutil
import pandas as pd
from historical_data_feeds.modules.data_source_base import DataSource
from libs.interfaces.utils.data_symbol import DataSymbol
from os import getenv
from libs.utils.singleton import singleton

# from historical_data_feeds.modules.utils import validate_dataframe_timestamps

@singleton
class DukascopyDataSource(DataSource):
    def __init__(self, logger=print):
        super().__init__(False, logger)

    def __get_ducascopy_interval(self, interval: str):
        if interval == 'tick': return 'tick'
        if interval == 'minute': return 'm1'
        if interval == 'minute5': return 'm5'
        if interval == 'minute15': return 'm15'
        if interval == 'minute30': return 'm30'
        if interval == 'hour': return 'h1'
        if interval == 'day': return 'd1'
        if interval == 'month': return 'mn1'


    async def validate_instrument_data(self, data: DataSymbol):
        # https://raw.githubusercontent.com/Leo4815162342/dukascopy-node/master/src/utils/instrument-meta-data/generated/raw-meta-data-2022-04-23.json
        # response = requests.get("http://api.open-notify.org/astros.json")
        from_datetime_timestamp = int(round(datetime.timestamp(data.backtest_date_start) * 1000))
        f = open('historical_data_feeds/temporary_ducascopy_list.json')
        instrument_list = load(f)['instruments']
        #validate if instrument exists:
        if data.symbol.upper() not in [v['historical_filename'] for k, v in instrument_list.items()]:
            self._log('Error. Instrument "'+data.symbol+'" does not exists on ducascopy.')
            return False

        # #validate it timestamps perios is right:
        # for k, v in instrument_list.items():
        #     if v["historical_filename"] == instrument.upper():
        #         first_timestamp = int(v["history_start_day"])
        #         if first_timestamp > from_datetime_timestamp:
        #             print("Error. First avaliable date of " , instrument, "is" , datetime.fromtimestamp(first_timestamp/1000.0))
        #             return False

        return True

    async def download_instrument_data(self, downloaded_data_path: str, instrument_file_name:str, instrument: str, interval: str, time_start: int, time_stop: int):
        self._log('_download_ducascopy_data', instrument_file_name)
        """
        documentation: 
        https://github.com/Leo4815162342/dukascopy-node
        """
        # try:
        duca_interval = self.__get_ducascopy_interval(interval)
        from_param = datetime.fromtimestamp(time_start//1000.0).strftime("%Y-%m-%d")
        to_param = datetime.fromtimestamp(time_stop//1000.0).strftime("%Y-%m-%d")
        cache_path = './cache_ducascopy'
        system('rm -r ' + cache_path)
        string_params = [
            ' -i '+ instrument,
            ' -from '+ from_param,
            ' -to '+ to_param,
            ' -s',
            ' -t ' + duca_interval,
            ' -fl', 
            ' -f csv',
            ' -dir '+ cache_path,
            ' -p bid'
        ]
        command = 'npx dukascopy-node'
        for param in string_params:
            command += param
        self._log('running command', command)
        system(command)
        name_of_created_file = next(walk(cache_path), (None, None, []))[2][0]  
        df = pd.read_csv(join(cache_path, name_of_created_file), index_col=None, header=None)
        if duca_interval == 'tick': 
            df = df.iloc[1:, [0,2]]
        else:
            df = df.iloc[1:, [0,1]]
        remove(join(cache_path, name_of_created_file))
        # if interval != STRATEGY_INTERVALS.tick.value:
        #     df = validate_dataframe_timestamps(df, interval, time_start, time_stop)
        df.to_csv(join(downloaded_data_path, instrument_file_name), index=False, header=False)
        # except Exception as e: 
        #     self._log('Excepted', e)
        #     return False
        return True
