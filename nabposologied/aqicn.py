# -*- coding: utf-8 -*-
"""
aqicn
"""

import json
import logging

import requests

AQICN_FEED = "http://api.waqi.info/feed/"
AQICN_TOKEN = "4cf7f445134f3fb69a4c3f0e5001e507a6cc386f"


class aqicnError(Exception):
    """Raise when errors occur while fetching or parsing data"""


class aqicnClient:
    """Client to fetch and parse data from aqicn"""

    def __init__(self, indice, latitude, longitude, update=False):
        """Initialize the client object."""
        self._posologie = 0
        self._city = "-"
        self._indice = indice
        self._latitude = latitude
        self._longitude = longitude
        if update:
            self.update()

    def update(self):
        """Fetch new data and format it"""
        self._fetch_posologie_data()

    def _aqicn_url(self, lat, lon):
        """Select AQICN URL to use"""
        if lat and lon:
            # Use geolocalized API
            return f"{AQICN_FEED}geo:{lat};{lon}/?token={AQICN_TOKEN}"
        else:
            # fallback to IP-based API
            return f"{AQICN_FEED}here/?token={AQICN_TOKEN}"

    def _fetch_posologie_data(self):
        try:
            result = requests.get(
                self._aqicn_url(self._latitude, self._longitude), timeout=10
            )
            raw_data = result.text
            json_data = json.loads(raw_data)
            logging.debug(f"data: {json_data}")
            city = json_data["data"]["city"]["name"]
            indice_aqi = json_data["data"]["aqi"]
            if "pm25" in json_data["data"]["iaqi"]:
                indice_pm25 = json_data["data"]["iaqi"]["pm25"]["v"]
            else:
                logging.info("no PM25 index available - using AQI index")
                indice_pm25 = indice_aqi
            logging.debug(
                f"Air quality indices from aqicn.org for {str(city)}"
                f" are: AQI={str(indice_aqi)} PM25= {str(indice_pm25)}"
                f" - selected index: {str(self._indice)}"
            )

            if self._indice == "aqi":
                indice_to_be_analyzed = indice_aqi
            elif self._indice == "pm25":
                indice_to_be_analyzed = indice_pm25
            else:
                indice_to_be_analyzed = indice_aqi

            try:
                if indice_to_be_analyzed > 100:
                    self._posologie = 0
                elif indice_to_be_analyzed > 50:
                    self._posologie = 1
                else:
                    self._posologie = 2
            except TypeError:
                """Invalid index: assume worst"""
                self._posologie = 0

            self._city = city

        except Exception as err:
            raise aqicnError(err)

    def get_data(self):
        return self._posologie

    def get_city(self):
        return self._city
