import functools
import logging
import time
from typing import Callable

from rosnik import constants
from rosnik.types.core import AIEvent, Metadata
from rosnik.wrap import wrap_class_method
from rosnik.types.ai import (
    AIFunctionMetadata,
    AIRequestFinish,
    AIRequestStart,
    ErrorResponseData,
    OpenAIAttributes,
)

try:
    from openai.openai_object import OpenAIObject
except ImportError as e:
    raise e

logger = logging.getLogger(__name__)

_OAI = "openai"


def serializer_with_metadata(
    serializer: Callable, generate_metadata: Callable[[], AIFunctionMetadata]
):
    """Each provider should be encapsulated into what it knows about the call."""
    return functools.partial(serializer, generate_metadata=generate_metadata)


def request_serializer(
    payload: dict,
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
) -> AIRequestStart:
    """`payload` is a dictionary of the `kwargs` provided to `create`.

    Given those kwargs and metadata, generate a AIRequestStart event.
    """
    if not payload:
        return None

    if generate_metadata is None:
        logger.warning("`generate_metadata` not provided. Bailing.")
        return

    # Reimport to make sure we have the latest values
    import openai

    metadata = generate_metadata()
    metadata.openai_attributes = OpenAIAttributes(
        api_base=openai.api_base,
        api_type=openai.api_type,
        api_version=openai.api_version,
        organization=openai.organization,
    )

    ai_model = (
        payload.get("model")
        if openai.api_type == "open_ai"
        else (payload.get("deployment_id") or payload.get("engine"))
    )
    user_id = payload.get("user")

    return AIRequestStart(
        ai_model=ai_model,
        ai_provider=metadata.ai_provider,
        ai_action=metadata.ai_action,
        ai_metadata=metadata,
        request_payload=payload,
        user_id=user_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )


def response_serializer(
    payload: "OpenAIObject",
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
) -> AIRequestFinish:
    if not payload:
        return None

    if generate_metadata is None:
        logger.warning("`generate_metadata` not provided. Bailing.")
        return

    # Reimport to make sure we have the latest values
    import openai

    # For both OpenAI and Azure, `model` contains the model on the response.
    ai_model = payload.get("model")
    metadata = generate_metadata()
    metadata.openai_attributes = OpenAIAttributes(
        api_base=openai.api_base,
        api_type=openai.api_type,
        api_version=openai.api_version,
        organization=openai.organization,
    )

    now = int(time.time_ns() / 1000000)
    return AIRequestFinish(
        ai_model=ai_model,
        ai_provider=metadata.ai_provider,
        ai_action=metadata.ai_action,
        ai_metadata=metadata,
        response_payload=payload,
        # Explicitly set this so that response_ms is stable.
        sent_at=now,
        response_ms=(now - prior_event.sent_at),
        ai_request_start_event_id=prior_event.event_id,
        user_id=prior_event.user_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )


def error_serializer(
    error: Exception,
    function_fingerprint: str,
    prior_event: AIEvent = None,
    generate_metadata: Callable[[], AIFunctionMetadata] = None,
) -> AIRequestFinish:
    if error is None:
        return None

    if generate_metadata is None:
        logger.warning("`generate_metadata` not provided. Bailing.")
        return

    import openai

    metadata = generate_metadata()
    metadata.openai_attributes = OpenAIAttributes(
        api_base=openai.api_base,
        api_type=openai.api_type,
        api_version=openai.api_version,
        organization=openai.organization,
    )

    now = int(time.time_ns() / 1000000)
    return AIRequestFinish(
        ai_model=None,
        ai_provider=metadata.ai_provider,
        ai_action=metadata.ai_action,
        ai_metadata=metadata,
        error_data=ErrorResponseData(
            message=str(error),
            json_body=getattr(error, "json_body", None),
            headers=getattr(error, "headers", None),
            organization=getattr(error, "organization", None),
            request_id=getattr(error, "request_id", None),
        ),
        response_ms=(now - prior_event.sent_at),
        ai_request_start_event_id=prior_event.event_id,
        user_id=prior_event.user_id,
        _metadata=Metadata(function_fingerprint=function_fingerprint),
    )


def _patch_completion(openai):
    if getattr(openai, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    wrap_class_method(
        openai.Completion,
        "create",
        serializer_with_metadata(
            request_serializer,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="completions"),
        ),
        serializer_with_metadata(
            response_serializer,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="completions"),
        ),
        serializer_with_metadata(
            error_serializer, lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="completions")
        ),
    )


def _patch_chat_completion(openai):
    if getattr(openai, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    wrap_class_method(
        openai.ChatCompletion,
        "create",
        serializer_with_metadata(
            request_serializer,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="chat.completions"),
        ),
        serializer_with_metadata(
            response_serializer,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="chat.completions"),
        ),
        serializer_with_metadata(
            error_serializer,
            lambda: AIFunctionMetadata(ai_provider=_OAI, ai_action="chat.completions"),
        ),
    )


def _patch_openai():
    try:
        import openai
    except ImportError as e:
        raise e

    if getattr(openai, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    if getattr(openai, "Completion", None):
        _patch_completion(openai)
    if getattr(openai, "ChatCompletion", None):
        _patch_chat_completion(openai)
    setattr(openai, f"__{constants.NAMESPACE}_patch", True)
