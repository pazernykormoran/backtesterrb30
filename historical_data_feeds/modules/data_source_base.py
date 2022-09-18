from abc import abstractmethod

class DataSource():

    def __init__(self, allow_synchronous_download: bool, logger=print):
        self._allow_synchronous_download = allow_synchronous_download
        self._log = logger

    @abstractmethod
    async def validate_instrument_data(data) -> bool:
        pass
    
    @abstractmethod
    async def download_instrument_data(self,
                        downloaded_data_path: str, 
                        instrument_file_name:str, 
                        instrument: str, 
                        interval: str, 
                        time_start: int, 
                        time_stop: int) -> bool:
        pass