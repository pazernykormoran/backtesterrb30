import pandas as pd

def get_interval_step_miliseconds(interval: str):
    print('ERROR, THIS FUNCTION IS NOT IMPLEMENTED')


def validate_dataframe_timestamps(df: pd.DataFrame, interval: str, time_start: int, time_stop: int):
    # print('starting validation: ', 'interval',interval , 'time_start',time_start , 'time_stop', time_stop)
    # print('-start in file name', datetime.fromtimestamp(time_start / 1000))
    # print('-stop in file name', datetime.fromtimestamp(time_stop / 1000))
    # print('is dividable???' ,( time_stop - time_start )/ timestamp_interval)
    # print('list timestamps first: ', list_timestamps[0], 'last: ', list_timestamps[-1])
    # print('-start in list', datetime.fromtimestamp(list_timestamps[0] / 1000))
    # print('-stop in list', datetime.fromtimestamp(list_timestamps[-1] / 1000))
    # print('proper len', len(list_timestamps))
    # print('head', df.head(2))
    # print('tail', df.tail(2))
    # print(df.dtypes)
    # print('iterating------')
    timestamp_interval = get_interval_step_miliseconds(interval)
    list_timestamps = range(time_start, time_stop, timestamp_interval)
    for i, timestamp in enumerate(list_timestamps):
        count = 0
        while int(df.iloc[i][0]) != int(timestamp):
            count+= 1
            df = pd.concat([df.iloc[:i],df.iloc[i-1:i],df.iloc[i:]], ignore_index=True)
            df.iloc[i,0] = int(timestamp)

    # for i, timestamp in enumerate(list_timestamps):
    #     if int(df.iloc[i][0]) != int(timestamp):
    #         print('Error during second validation of data. Timestamps are not equal. Stopping')
    #         self._stop()

    # if df.shape[0] != len(list_timestamps):
    #     print('Error. Data frame length is not proper after validation. Check "validate_dataframe_timestamps" function')
    #     self._stop()
    return df
