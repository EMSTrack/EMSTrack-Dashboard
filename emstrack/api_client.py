from typing import Union

import requests


class ApiClient:

    def __init__(self, base_url: str = '/'):
        self._base_url = base_url
        self._token = None

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value: str):
        self._token = value

    @property
    def base_url(self):
        return self._base_url

    @base_url.setter
    def base_url(self, value: str):
        self._base_url = value

    def get_json_header(self) -> dict:
        return {'accept': 'application/json', 'Content-Type': 'application/json'} if self._token is None \
            else {'accept': 'application/json', 'Content-Type': 'application/json',
                  'Authorization': f'Token {self._token}'}

    def get_json(self, url: str, **kwargs) -> Union[str, dict, list]:
        """
        Method for a generic HTTP GET request
        Args:
            url: string, url for GET request
        Kwargs: other parameters to get
        Returns:
            A json object containing HTTP GET response.
        """
        response = requests.get(self._base_url + url, headers=self.get_json_header(), **kwargs)
        response.raise_for_status()
        return response.json()

    def post_json(self, url: str, **kwargs) -> Union[str, dict, list]:
        """
        Method for a generic HTTP POST request
        Args:
            url: string, url for POST request
        Kwargs: other parameters to put
        Returns:
            A json object containing HTTP POST response.
        """
        response = requests.post(self._base_url + url, headers=self.get_json_header(), **kwargs)
        response.raise_for_status()
        return response.json()
