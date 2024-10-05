from backtesterrb30.libs.utils.run_service import run_service

from backtesterrb30.live_data_feeds.live_data_feeds import LiveDataFeeds

microservice_name = "live_data_feeds"

run_service(microservice_name, LiveDataFeeds)
