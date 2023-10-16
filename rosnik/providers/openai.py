import logging

from rosnik import constants
from rosnik.wrap import wrap_class_method
from rosnik.types.ai import AIFunctionMetadata, ErrorResponseData, OpenAIAttributes, ResponseData

try:
    from openai.openai_object import OpenAIObject
    from openai import OpenAIError
except ImportError as e:
    raise e

logger = logging.getLogger(__name__)

_OAI = "openai"
completion_metadata = AIFunctionMetadata(ai_provider=_OAI, ai_action="completions")
chat_completion_metadata = AIFunctionMetadata(ai_provider=_OAI, ai_action="chat.completions")


def response_serializer(payload: "OpenAIObject") -> ResponseData:
    if not payload:
        return None

    return ResponseData(
        response_payload=payload.to_dict_recursive(),
        organization=payload.organization,
        response_ms=payload.response_ms,
    )


def error_serializer(error: Exception) -> ErrorResponseData:
    if error is None:
        return None

    if isinstance(error, OpenAIError):
        return ErrorResponseData(
            message=error._message,
            json_body=error.json_body,
            headers=error.headers,
            http_status=error.http_status,
            organization=error.organization,
            request_id=error.request_id,
        )

    return ErrorResponseData(message=str(error))


def _patch_completion(openai):
    if getattr(openai, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    completion_metadata.openai_attributes = OpenAIAttributes(
        api_base=openai.api_base, api_type=openai.api_type, api_version=openai.api_version
    )

    wrap_class_method(
        openai.Completion, "create", completion_metadata, response_serializer, error_serializer
    )


def _patch_chat_completion(openai):
    if getattr(openai, f"__{constants.NAMESPACE}_patch", False):
        logger.warning("Not patching. Already patched.")
        return

    chat_completion_metadata.openai_attributes = OpenAIAttributes(
        api_base=openai.api_base, api_type=openai.api_type, api_version=openai.api_version
    )

    wrap_class_method(
        openai.ChatCompletion,
        "create",
        chat_completion_metadata,
        response_serializer,
        error_serializer,
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
