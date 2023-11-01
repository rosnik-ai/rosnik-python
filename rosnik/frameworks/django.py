from rosnik import client, headers, state

try:
    from django.conf import settings
except ImportError:
    settings = None


def _to_django_header(key):
    """Converts our header key to a Django header key."""
    return f'HTTP_{key.replace("-", "_").upper()}'


def rosnik_middleware(get_response):
    # Initialize our SDK at the start using Django settings.
    client.init(
        api_key=getattr(settings, "ROSNIK_API_KEY", None),
        sync_mode=getattr(settings, "ROSNIK_SYNC_MODE", None),
        environment=getattr(settings, "ROSNIK_ENVIRONMENT", None),
        event_context_hook=getattr(settings, "ROSNIK_EVENT_CONTEXT_HOOK", None),
    )

    def middleware(request):
        """Each request is considered a distinct Journey, unless a Journey ID is supplied."""
        journey_id = request.META.get(_to_django_header(headers.JOURNEY_ID_KEY))
        if journey_id is None:
            journey_id = state.create_journey_id()
        state.store(state.State.JOURNEY_ID, journey_id)

        interaction_id = request.META.get(_to_django_header(headers.INTERACTION_ID_KEY))
        state.store(state.State.USER_INTERACTION_ID, interaction_id)

        device_id = request.META.get(_to_django_header(headers.DEVICE_ID_KEY))
        state.store(state.State.DEVICE_ID, device_id)

        response = get_response(request)

        # Pass our Journey ID back to the client,
        # so we can use it for subsequent requests.
        response[headers.JOURNEY_ID_KEY] = state.get_journey_id()
        return response

    return middleware
