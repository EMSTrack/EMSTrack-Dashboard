from datetime import date, timedelta
from typing import Optional, Dict, cast, Iterable

import numpy as np
import pandas as pd
from haversine import haversine_vector, Unit

from emstrack.api_client import ApiClient
from utils import generate_new_color


def retrieve_ambulance_data(api_client: ApiClient, end: date = date.today(), start: Optional[date] = None) -> Dict[int, dict]:
    """
    Retrieve ambulance data from the EMSTrack API

    The resulting dictionary contains the ambulance data as obtained from the API plus and additional key 'data'
    containing a pandas datafrome with the ambulance data in the range start-end.

    If the start date is None then it is set to the day before end date.

    The dataframe has the following columns:
        status, orientation, timestamp, updated_by_username, updated_on, location.latitude, location.longitude
    Some rows might have null entries. The dataframe is sorted in ascending order of timestamp.

    Args:
        api_client: an ApiClient instance
        end: the end date to fetch (default: today)
        start: the end date to fetch (default: None)

    Returns:
        a dictionary with ambulance data indexed by the ambulance id
    """

    if start is None:
        # default start to the day before end
        start = end - timedelta(days=1)
    elif end < start:
        # swap dates if needed
        end, start = start, end

    # retrieve ambulances and create a dictionary indexed by ambulance id
    ambulances = {ambulance['id']: ambulance for ambulance in cast(list, api_client.get_json('ambulance'))}

    for ambulance_id, ambulance in ambulances.items():

        # retrieve ambulance data
        # TODO: make it UTC aware
        data = cast(list,
                    api_client.get_json(f'ambulance/{ambulance_id}/updates',
                                        params={'filter':
                                                    f'{start.isoformat()}T00:00:00.000Z,{end.isoformat()}T00:00:00.000Z'}))

        # normalize data in dataframe
        df = pd.json_normalize(data)
        if 'location' in df.columns:
            # data came with empty locations, make sure location is normalized correctly
            df['location.latitude'] = df['location']
            df['location.longitude'] = df['location']
            df.drop(columns='location')
        if 'location.latitude' not in df.columns or 'location.longitude' not in df.columns:
            # data came with empty locations, make sure location is normalized correctly
            df['location.latitude'] = None
            df['location.longitude'] = None
        if 'status' not in df.columns:
            # data came with empty locations, make sure location is normalized correctly
            df['status'] = None
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        else:
            df = pd.DataFrame(columns=['status', 'orientation',
                                       'updated_by_username', 'updated_on',
                                       'location.latitude', 'location.longitude'])

        # store in ambulance with new color
        ambulance.update({'data': df,
                          'ambulance_color': generate_new_color()})

    return ambulances

def segment_ambulance_data(df: pd.DataFrame, threshold_distance_m: float, threshold_time_s: float) -> pd.DataFrame:
    """
    Use this function to segment a dataframe obtained with retrieve_ambulance_data.

    Segmentation is done based on threshold distance and time.

    Args:
        df: the dataframe with ambulance data assumed to be sorted in ascending order of timestamp
        threshold_distance_m: the maximum distance in meters between two data points that is considered too far to be in the same segment
        threshold_time_s: the maximum time in s between two data points that is considered too far to be in the same segment

    Returns:
        the original dataframe augmented with the columns:
            distance_m: the distance in meters between consecutive data points
            timedelta_s: the time distance in s between consecutive data points
            segment: the index of the segment of a set of points
    """

    # remove rows without location
    df = df.dropna(subset=['location.latitude', 'location.longitude'])
    if df.empty:
        return pd.DataFrame(columns = df.columns.tolist() + ['distance_m', 'timedelta_s', 'segment'])
    elif len(df) == 1:
        df['distance_m'] = 0
        df['timedelta_s'] = 0
        df['segment'] = 0
        return df

    # calculate distances
    distance = haversine_vector(df[['location.latitude', 'location.longitude']][:-1].values,
                                df[['location.latitude', 'location.longitude']][1:].values, Unit.METERS)
    times = (df.index[:-1].values - df.index[1:].values)/np.timedelta64(1,'s')

    # augment dataframe
    df['distance_m'] = np.insert(distance, 0, 0)
    df['timedelta_s'] = np.insert(times, 0, 0)
    df['segment'] = 0

    # segment
    df['segment'] = np.cumsum(np.logical_or(df['distance_m'] > threshold_distance_m, df['timedelta_s'] > threshold_time_s).astype(int))

    return df

# def sample_ambulance_data(df : pd.DataFrame, steps: Iterable[np.datetime64]) -> pd.DataFrame:
#     # replicate dataframe data
#     dfs = pd.DataFrame(columns=df.columns)
#     for datetime in steps:

