from datetime import timezone
from backtesterRB30.libs.interfaces.utils.data_schema import DataSchema


def validate_config(config: dict):
    cfg = DataSchema(**config)
    for symbol in cfg.data:
        symbol.backtest_date_start = symbol.backtest_date_start.replace(tzinfo=timezone.utc)
        symbol.backtest_date_stop = symbol.backtest_date_stop.replace(tzinfo=timezone.utc)
    return cfg