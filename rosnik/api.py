import logging
from urllib3.util import Retry

from rosnik import config
from rosnik.types import core

import requests
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)

_base_url = "https://ingest.rosnik.ai/api/v1/events"

_NUM_RETRIES = 3

_retry_status_code = [429, 500, 502, 503, 504]
retry_strategy = Retry(
    total=_NUM_RETRIES,
    backoff_factor=1,
    status_forcelist=_retry_status_code,
    allowed_methods=["POST"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


class IngestClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.mount("https://", adapter)

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {config.Config.api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, *args, **kwargs):
        # Wait up to 3 seconds before giving up
        kwargs["timeout"] = 3
        return self.session.post(*args, **kwargs)

    def send_event(self, event: core.Event, url=_base_url):
        logger.debug(
            f"Sending {event.event_type} event to {url} with event ID {event.event_id} and journey ID {event.journey_id}"  # noqa
        )
        try:
            response = self._post(url, headers=self.headers, json=event.to_dict())
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Failed to send event: {e}")
        except requests.exceptions.RetryError as e:
            logger.warning(f"Failed to send event after {_NUM_RETRIES} attempts: {e}")
