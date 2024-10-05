from datetime import datetime, timezone


def datetime_to_timestamp(datetime: datetime):
    if datetime.tzinfo is None or datetime.tzinfo.utcoffset(datetime) is None:
        datetime = datetime.replace(tzinfo=timezone.utc)
    return(int(datetime.timestamp() * 1000))

def timestamp_to_datetime(timestamp: int):
    return datetime.utcfromtimestamp(timestamp/1000)