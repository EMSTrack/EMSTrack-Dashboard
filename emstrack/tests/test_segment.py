import unittest
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from emstrack.util import segment_ambulance_data, sample_ambulance_data


class TestSegment(unittest.TestCase):

    def test_segment(self):

        # setup data for testing
        paris = (48.8567, 2.3508)
        new_york = (40.7033962, -74.2351462)
        lyon = (45.7597, 4.8422)  # (lat, lon)

        now = datetime.now()
        data = {'location.latitude': [lyon[0], lyon[0], lyon[0], paris[0], new_york[0]],
                'location.longitude': [lyon[1], lyon[1], lyon[1], paris[1], new_york[1]],
                'timestamp': [now, now - timedelta(seconds=20), now - timedelta(seconds=30), now - timedelta(seconds=40), now - timedelta(seconds=50)]}
        df = pd.DataFrame(data=data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)

        # segment data
        dfs = segment_ambulance_data(df, 300000, 15)
        np.testing.assert_allclose(dfs['distance_m'], [0, 5853300, 392200, 0, 0], 1e-1)
        np.testing.assert_allclose(dfs['timedelta_s'], [0, 10, 10, 10, 20])
        np.testing.assert_allclose(dfs['segment'], [0, 1, 2, 2, 3])

        # segment again
        dfs = segment_ambulance_data(dfs, 300000, 15)
        np.testing.assert_allclose(dfs['distance_m'], [0, 5853300, 392200, 0, 0], 1e-1)
        np.testing.assert_allclose(dfs['timedelta_s'], [0, 10, 10, 10, 20])
        np.testing.assert_allclose(dfs['segment'], [0, 1, 2, 2, 3])

    def test_sample(self):

        # setup data for testing
        paris = (48.8567, 2.3508)
        new_york = (40.7033962, -74.2351462)
        lyon = (45.7597, 4.8422)  # (lat, lon)

        now = datetime.now()
        data = {'location.latitude': [lyon[0], lyon[0], lyon[0], paris[0], new_york[0]],
                'location.longitude': [lyon[1], lyon[1], lyon[1], paris[1], new_york[1]]}
        timestamp = pd.DatetimeIndex([now, now - timedelta(seconds=20), now - timedelta(seconds=30), now - timedelta(seconds=40), now - timedelta(seconds=45)])
        df = pd.DataFrame(data=data, index=timestamp)
        df.sort_index(inplace=True)
        print(df)

        # sample data
        dfs = sample_ambulance_data(df, pd.DatetimeIndex(pd.date_range(now - timedelta(seconds=50), now, 2)))
        print(dfs)

        dfs = sample_ambulance_data(df, pd.DatetimeIndex(pd.date_range(now - timedelta(seconds=50), now, 3)))
        print(dfs)

        dfs = sample_ambulance_data(df, pd.DatetimeIndex(pd.date_range(now - timedelta(seconds=50), now, 4)))
        print(dfs)

        dfs = sample_ambulance_data(df, pd.DatetimeIndex(pd.date_range(now - timedelta(seconds=50), now, 5)))
        print(dfs)
