from backtesterrb30.libs.utils.run_service import run_service
from backtesterrb30.historical_data_feeds.historical_data_feeds import (
    HistoricalDataFeeds,
)

microservice_name = "historical_data_feeds"

run_service(microservice_name, HistoricalDataFeeds)
