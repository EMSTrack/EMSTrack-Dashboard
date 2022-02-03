from datetime import datetime, date, timedelta
from typing import List, Dict, Any, cast

import pandas as pd

from emstrack.api_client import ApiClient
from utils import generate_new_color


class EMSTrackData:

    def __init__(self):
        self._ambulances = {}

    @property
    def ambulances(self):
        return self._ambulances

    def retrieve_data(self, api_client: ApiClient, end: date = date.today(), start: date = date.today() - timedelta(days=1)):

        if end < start:
            # swap dates if needed
            end, start = start, end

        # retrieve ambulances and create a dictionary indexed by ambulance id
        ambulances = cast(list, api_client.get_json('ambulance'))
        self._ambulances = {ambulance['id']: ambulance for ambulance in ambulances}

        for ambulance_id, ambulance in self._ambulances.items():

            # retrieve ambulance data
            # TODO: make it UTC aware
            data = cast(list,
                        api_client.get_json(f'ambulance/{ambulance_id}/updates',
                                            params={'filter':
                                                        f'{start.isoformat()}T00:00:00.000Z,{end.isoformat()}T00:00:00.000Z'}))

            # store in dataframe and add color
            ambulance.update({'data': pd.DataFrame(data),
                              'ambulance_color': generate_new_color()})
