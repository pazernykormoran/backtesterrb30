import pandas as pd

def validate_dataframe_timestamps(df: pd.DataFrame, 
            interval_step_miliseconds: int, time_start: int, time_stop: int) -> pd.DataFrame:
    try:
        if interval_step_miliseconds > 1000*60*60*24: 
            print('cannot validate df with this interval')
            return df
        timestamp_interval = interval_step_miliseconds
        list_timestamps = range(time_start, time_stop, timestamp_interval)
        for i, timestamp in enumerate(list_timestamps):
            if i == 0: continue
            count = 0
            while int(df.iloc[i][0]) != int(timestamp):
                count+= 1
                df = pd.concat([df.iloc[:i],df.iloc[i-1:i],df.iloc[i:]], ignore_index=True)
                df.iloc[i,0] = int(timestamp)
    except IndexError:
        pass
    return df
