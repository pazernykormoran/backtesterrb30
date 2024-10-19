import asyncio
import time as tm
from os import listdir, makedirs, path
from os.path import isfile, join
from typing import List

from backtesterrb30.historical_data_feeds.functions import (
    get_instrument_files,
    load_data_frame_ticks_2,
)
from backtesterrb30.historical_data_feeds.historical_downloader import (
    HistoricalDownloader,
)
from backtesterrb30.libs.communication_broker.broker_base import BrokerBase
from backtesterrb30.libs.data_sources.data_sources_list import HISTORICAL_SOURCES
from backtesterrb30.libs.interfaces.historical_data_feeds.instrument_file import (
    InstrumentFile,
)
from backtesterrb30.libs.interfaces.python_backtester.data_start import DataStart
from backtesterrb30.libs.interfaces.utils.config import Config
from backtesterrb30.libs.interfaces.utils.data_schema import DataSchema
from backtesterrb30.libs.utils.list_of_services import SERVICES, SERVICES_ARRAY
from backtesterrb30.libs.utils.service import Service


class HistoricalDataFeeds(Service):
    _broker: BrokerBase

    def __init__(
        self, config: Config, data_schema: DataSchema, loop=None, logger=print
    ):
        super().__init__(config, logger)
        self._log("Cache directory", config.cache_dir)
        self.config: Config = config
        self.__loop = loop
        self.__custom_event_loop = False
        if self.__loop is None:
            self.__loop = asyncio.get_event_loop()
            self.__custom_event_loop = True
        self.__data_schema: DataSchema = data_schema
        self.__columns = ["timestamp"] + [c.symbol for c in self.__data_schema.data]
        self.__historical_sources_array = [
            i for i in dir(HISTORICAL_SOURCES) if not i.startswith("__")
        ]
        self.__data_sources = {}
        self.__sending_locked = False
        self.__start_time = 0
        self.__data_to_download_2 = None
        self.__engine_ready = False
        self.__historical_downloader = HistoricalDownloader(
            self.__data_schema,
            self.__historical_sources_array,
            self.config.cache_dir,
            self._log,
        )

    # # override
    # def _asyncio_loop(self, loop: asyncio.AbstractEventLoop):
    #     self._create_listeners(loop)
    #     self.__validate_downloaded_data_folder()
    #     if self.config.backtest:
    #         self.__data_to_download_2 = self.__historical_downloader.run(loop)
    #         data_parts = self.__prepare_loading_data_structure_2()
    #         loop.create_task(self.__historical_data_loop_ticks(data_parts))
    #     else:
    #         self._log('backtest is off')

    def _loop(self):
        # self._broker.run()
        self._broker.create_listeners(self.__loop)
        self.__validate_downloaded_data_folder()
        if self.config.backtest:
            self.__data_to_download_2 = self.__historical_downloader.run(self.__loop)
            data_parts = self.__prepare_loading_data_structure_2()
            self.__loop.create_task(self.__historical_data_loop_ticks(data_parts))
        else:
            self._log("backtest is off")
        if self.__custom_event_loop:
            self.__loop.run_forever()
            self.__loop.close()

    # def _send(self, service: SERVICES, msg: str, *args):
    #     self._broker.send(service, msg, *args)

    def _configure(self):
        super()._configure()
        # register commands
        self._broker.register(
            "unlock_historical_sending", self.__unlock_historical_sending_event
        )
        self._broker.register(
            "engine_ready_response", self.__engine_ready_response_event
        )

    # # override
    # def _handle_zmq_message(self, message):
    #     pass

    async def __send_start_params(self):
        self.__start_time = tm.time()
        file_names_grouped = []
        for symbol in self.__data_schema.data:
            file_names_grouped.append(
                {
                    "symbol": symbol.symbol,
                    "source": symbol.historical_data_source,
                    "files": get_instrument_files(symbol),
                }
            )
        start_params = {
            "file_names": file_names_grouped,
            "start_time": self.__start_time,
        }
        await self._broker.send(
            SERVICES.python_backtester, "data_start", DataStart(**start_params)
        )

    async def __historical_data_loop_ticks(self, data_parts: dict):
        # waiting for zero mq ports starts up
        await asyncio.sleep(0.5)
        while True:
            # if self.__data_downloaded(self.__data_to_download):
            await self._broker.send(
                SERVICES.python_engine,
                "engine_ready",
                SERVICES.historical_data_feeds.value,
            )
            if (
                self.__validate_data_downloaded(self.__data_to_download_2)
                and self.__engine_ready
            ):
                self._log("All data has been downloaded")

                sending_counter = 0
                self._log("Starting data loop")
                await self.__send_start_params()
                # return
                last_row = []
                for _, one_year_array in data_parts.items():
                    self._log("Synchronizing part of data")
                    data_part = load_data_frame_ticks_2(
                        self.__data_schema,
                        self.__columns,
                        self.config.cache_dir,
                        last_row,
                        one_year_array,
                    )
                    for row in data_part:
                        last_row = row
                        await self._broker.send(
                            SERVICES.python_engine, "data_feed", list(last_row)
                        )
                        sending_counter += 1
                        if sending_counter % 1000 == 0:
                            self.__sending_locked = True
                            await self._broker.send(
                                SERVICES.python_engine, "historical_sending_locked"
                            )
                            while self.__sending_locked:
                                await asyncio.sleep(0.01)

                await self._broker.send(SERVICES.python_engine, "data_finish")
                break
            await asyncio.sleep(1)

    def __validate_data_downloaded(self, files_to_download: List[InstrumentFile]):
        if files_to_download is None:
            return False
        files_in_directory = [
            f
            for f in listdir(self.config.cache_dir)
            if isfile(join(self.config.cache_dir, f))
        ]
        data_to_download = list(
            set([f.to_filename() for f in files_to_download]) - set(files_in_directory)
        )
        return data_to_download == []

    def __validate_downloaded_data_folder(self):
        if not path.exists(self.config.cache_dir):
            makedirs(self.config.cache_dir)

    def __prepare_loading_data_structure_2(self) -> dict:
        files_collection = {}
        for symbol in self.__data_schema.data:
            files: List[InstrumentFile] = get_instrument_files(symbol)
            for f in files:
                if f.time_stop not in files_collection:
                    files_collection[f.time_stop]: List[InstrumentFile] = []
                files_collection[f.time_stop].append(f)
        return dict(sorted(files_collection.items()))

    async def __stop_all_services(self):
        for service in SERVICES_ARRAY:
            if service != self.name:
                await self._broker.send(getattr(SERVICES, service), "stop")
        self._broker.stop()

    # COMMANDS

    async def __unlock_historical_sending_event(self):
        self.__sending_locked = False

    async def __engine_ready_response_event(self):
        self.__engine_ready = True
