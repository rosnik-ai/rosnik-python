import logging
from rosnik.types.ai import AIFunctionMetadata

from rosnik import env
from rosnik.wrap import wrap_class_method

logger = logging.getLogger(__name__)

try:
    from openai.openai_object import OpenAIObject
except ImportError:
    OpenAIObject = dict
    logger.warning("openai is not installed")

_OAI = "openai"
completion_metadata: AIFunctionMetadata = {"ai_provider": _OAI, "ai_action": "completions"}
chat_completion_metadata: AIFunctionMetadata = {
    "ai_provider": _OAI,
    "ai_action": "chat.completions",
}


def response_serializer(payload: 'OpenAIObject'):
    return payload.to_dict()


def _patch_completion(openai):
    if getattr(openai, f"__{env.NAMESPACE}_patch", False):
        logger.debug("Not patching. Already patched.")
        return

    openai_attributes = {}
    openai_attributes["api_base"] = openai.api_base
    openai_attributes["api_type"] = openai.api_type
    openai_attributes["api_version"] = openai.api_version
    completion_metadata["openai_attributes"] = openai_attributes

    openai.Completion.create = wrap_class_method(completion_metadata, response_serializer)(openai.Completion.create)


def _patch_chat_completion(openai):
    if getattr(openai, f"__{env.NAMESPACE}_patch", False):
        logger.debug("Not patching. Already patched.")
        return

    openai_attributes = {}
    openai_attributes["api_base"] = openai.api_base
    openai_attributes["api_type"] = openai.api_type
    openai_attributes["api_version"] = openai.api_version
    chat_completion_metadata["openai_attributes"] = openai_attributes

    openai.ChatCompletion.create = wrap_class_method(
        chat_completion_metadata, response_serializer
    )(openai.ChatCompletion.create)


def _patch_openai():
    import openai

    if getattr(openai, f"__{env.NAMESPACE}_patch", False):
        logger.debug("Not patching. Already patched.")
        return

    if getattr(openai, "Completion", None):
        _patch_completion(openai)
    if getattr(openai, "ChatCompletion", None):
        _patch_chat_completion(openai)
    setattr(openai, f"__{env.NAMESPACE}_patch", True)
