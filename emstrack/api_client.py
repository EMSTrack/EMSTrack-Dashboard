from typing import Union, Optional

import requests


class ApiClient:
    """
    ApiClient is a convenience class to make json http requests using a DRF token
    """

    def __init__(self, base_url: str = '/'):
        """
        Constructor for ApiClient

        Args:
            base_url: the base url (default: '/')
        """
        self._base_url = base_url
        self._token = None

    @property
    def token(self) -> Optional[str]:
        """
        Get token

        Returns:
            the token
        """
        return self._token

    @token.setter
    def token(self, value: str):
        """
        Set token

        Args:
            value: the value of the token

        Returns:
            None
        """
        self._token = value

    @property
    def base_url(self) -> str:
        """
        Get base url

        Returns:
            the base url
        """
        return self._base_url

    @base_url.setter
    def base_url(self, value: str):
        """
        Set base url

        Args:
            value: the base url

        Returns:
            None
        """
        self._base_url = value

    def get_json_header(self) -> dict:
        """
        Get json header

        Returns:
            a suitable header for json http requests
        """
        return {'accept': 'application/json', 'Content-Type': 'application/json'} if self._token is None \
            else {'accept': 'application/json', 'Content-Type': 'application/json',
                  'Authorization': f'Token {self._token}'}

    def get_json(self, url: str, **kwargs) -> Union[str, dict, list]:
        """
        HTTP GET json request

        Args:
            url: string, url for GET request
            kwargs: other parameters to get

        Returns:
            a json object containing HTTP GET response.
        """
        response = requests.get(self._base_url + url, headers=self.get_json_header(), **kwargs)
        response.raise_for_status()
        return response.json()

    def post_json(self, url: str, **kwargs) -> Union[str, dict, list]:
        """
        HTTP POST json request

        Args:
            url: string, url for POST request
            kwargs: other parameters to put

        Returns:
            a json object containing HTTP POST response.
        """
        response = requests.post(self._base_url + url, headers=self.get_json_header(), **kwargs)
        response.raise_for_status()
        return response.json()
