import os
import unittest
from datetime import date, timedelta

import dateutil.utils

from emstrack.api_client import ApiClient
from emstrack.data import EMSTrackData


class TestApiClientAndEMSTrackData(unittest.TestCase):

    def get_base_url_and_set_token(self):

        base_url = os.environ['DASHBOARD_SERVER_URL']
        username = os.environ['MQTT_USERNAME']
        password = os.environ['MQTT_PASSWORD']
        api_client = ApiClient(base_url)
        json = api_client.post_json('en/auth/token/', json={'username': username, 'password': password})
        self.assertIsInstance(json, dict)
        self.assertTrue('token' in json)
        api_client.token = json['token']
        return api_client, base_url

    def test_properties(self):

        api_client = ApiClient()
        self.assertEqual(api_client.get_json_header(),
                         {'accept': 'application/json', 'Content-Type': 'application/json'})

        api_client.token = '123'
        self.assertEqual(api_client.token, '123')
        self.assertEqual(api_client.get_json_header(),
                         {'accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Token 123'})

    def test_post_json_get_token(self):

        api_client, base_url = self.get_base_url_and_set_token()
        self.assertIsInstance(api_client, ApiClient)
        self.assertIsInstance(base_url, str)

    def test_get_ambulances(self):

        api_client, base_url = self.get_base_url_and_set_token()
        api_client.base_url = base_url + 'api/'
        self.assertEqual(api_client.base_url, base_url + 'api/')

        json = api_client.get_json('ambulance/')
        self.assertTrue(isinstance(json, list))
        if len(json) > 0:
            ambulance = json[0]
            self.assertTrue(isinstance(ambulance, dict))
            self.assertTrue('id' in ambulance)

    def test_get_data(self):

        api_client, base_url = self.get_base_url_and_set_token()
        api_client.base_url = base_url + 'api/'
        self.assertEqual(api_client.base_url, base_url + 'api/')

        data = EMSTrackData()
        data.retrieve_data(api_client)
        self.assertIsInstance(data.ambulances, dict)

        end = date.today()
        start = date.today() - timedelta(days=1)
        data.retrieve_data(api_client, start, end)
        self.assertIsInstance(data.ambulances, dict)

        data.retrieve_data(api_client, end, start)
        self.assertIsInstance(data.ambulances, dict)
