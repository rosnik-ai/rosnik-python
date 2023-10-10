import logging
import os
from rosnik import env

from rosnik.types import core

import requests

logger = logging.getLogger(__name__)

_base_url = "https://ingest.rosnik.ai/api/v1/events"


class IngestClient:
    def __init__(self):
        self.api_key = env.get_api_key()
        if self.api_key is None:
            logger.warning(f"{env.API_KEY} is not set and an API token was not provided on init")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.session = requests.Session()

    def _post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    def send_event(self, event: core.Event):
        logger.debug(f"Sending event to {_base_url}")
        print(f"Sending event to {_base_url}")
        print("Event", event.to_json())
        print("Headers", self.headers)
        try:
            response = self._post(_base_url, headers=self.headers, json=event.to_json())
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.warning("Failed to send event:", e)
