import logging
import os

from prompthq import types

import requests

logger = logging.getLogger(__name__)

# TODO: use the prompthq.ai domain
_base_url = "https://ingest-xb6xg3ggrq-uc.a.run.app/api/v1/ingest"


# TODO: add env, lang.
class PromptHqHttpClient:
    def __init__(self, api_key=None):
        self.api_key = os.environ.get("PROMPTHQ_API_KEY", api_key)
        if self.api_key is None:
            logger.warning("PROMPTHQ_API_KEY is not set and an API token was not provided on init")

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.session = requests.Session()

    def send_event(self, event: types.PromptHqEvent):
        platform = event["_prompthq_metadata"]["platform"]
        action = event["_prompthq_metadata"]["action"]
        url = f"{_base_url}/{platform}/{action}"
        logger.debug(f"Sending event to {url}")
        try:
            response = self.session.post(url, headers=self.headers, json=event)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.warning("Failed to send PromptHQ event:", e)
