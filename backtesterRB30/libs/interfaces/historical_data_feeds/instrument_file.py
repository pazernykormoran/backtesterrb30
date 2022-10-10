from datetime import datetime
# from symbol import parameters
from pydantic import BaseModel
from enum import Enum
# from backtesterRB30.libs.utils.historical_sources import HISTORICAL_SOURCES, HISTORICAL_INTERVALS_UNION
from backtesterRB30.libs.utils.timestamps import datetime_to_timestamp

class InstrumentFile(BaseModel):
    source: str
    instrument: str
    interval: str
    time_start: int
    time_stop: int

    @property
    def identifier(self):
        return self.source + "_" + self.instrument


    @classmethod
    def from_filename(cls, filename: str):
        if not filename or filename == '': 
            raise Exception('Empty file name name')
        if filename[-4:] != '.csv': 
            raise Exception('Bad file extension')
        filename = filename[:-4]
        source, instrument, interval, time_start, time_stop = tuple(filename.split('__'))
        if None in (source, instrument, interval, time_start, time_stop) or \
                '' in (source, instrument, interval, time_start, time_stop):
            raise Exception('Bad file name string provided')
        dict_instrument_file = {
            'source': source,
            'instrument': instrument,
            'interval': interval,
            'time_start': int(time_start),
            'time_stop': int(time_stop)
        }
        return cls(**dict_instrument_file)
    
    @classmethod
    def from_params(cls, 
                source: str, 
                instrument: str, 
                interval: Enum, 
                time_start: datetime,
                time_stop: datetime):
        dict_instrument_file = {
            'source': source,
            'instrument': instrument,
            'interval': interval.value,
            'time_start': datetime_to_timestamp(time_start),
            'time_stop': datetime_to_timestamp(time_stop)
        }
        return cls(**dict_instrument_file)

    def to_filename(self):
        return self.source + "__" \
            + self.instrument  + "__" \
            + self.interval  + "__" \
            + str(self.time_start)  + "__" \
            + str(self.time_stop) + ".csv"
        
    def __str__(self):
        return self.to_filename()

    def toJSON(self):
        return self.to_filename()

    # def get_file_name() -> str:
