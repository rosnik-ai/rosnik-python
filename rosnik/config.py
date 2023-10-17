import os
from rosnik import constants

API_KEY = f"{constants.NAMESPACE}_API_KEY"
# If set to a non-0 value,
# we will send values synchronously.
SYNC_MODE = f"{constants.NAMESPACE}_SYNC_MODE"
ENVIRONMENT = f"{constants.NAMESPACE}_ENVIRONMENT"


class _Config:
    def __init__(self, api_key=None, sync_mode=None, environment=None, event_context_hook=None):
        self._api_key = api_key or os.environ.get(API_KEY)
        _sync = sync_mode or os.environ.get(SYNC_MODE)
        self._sync_mode = _sync and _sync != "0"
        self._environment = environment or os.environ.get(ENVIRONMENT)
        self._event_context_hook = event_context_hook

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value):
        if self._api_key is not None:
            return
        self._api_key = value

    @property
    def sync_mode(self):
        return bool(self._sync_mode)

    @sync_mode.setter
    def sync_mode(self, value):
        if self._sync_mode is not None:
            return
        self._sync_mode = value

    @property
    def environment(self):
        return self._environment

    @environment.setter
    def environment(self, value):
        if self._environment is not None:
            return
        self._environment = value

    @property
    def event_context_hook(self):
        return self._event_context_hook

    @event_context_hook.setter
    def event_context_hook(self, value):
        if self._event_context_hook is not None:
            return
        self._event_context_hook = value


Config = _Config()
