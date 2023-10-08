import logging
from rosnik.types.ai import AIFunctionMetadata

from rosnik.wrap import wrap_class_method
from rosnik.types.core import Metadata

logger = logging.getLogger(__name__)

try:
    from openai.openai_object import OpenAIObject
except ImportError:
    OpenAIObject = dict
    logger.warning("openai is not installed")

_OAI = "openai"
completion_metadata: AIFunctionMetadata = {"ai_provider": _OAI, "ai_action": "completion"}
chat_completion_metadata: AIFunctionMetadata = {"ai_provider": _OAI, "ai_action": "chatcompletion"}


def _patch_completion(openai):
    openai.Completion.create = wrap_class_method(openai.Completion.create, completion_metadata)


def _patch_chat_completion(openai):
    openai.ChatCompletion.create = wrap_class_method(
        openai.ChatCompletion.create, chat_completion_metadata
    )


def _patch_openai(openai=None):
    if not openai:
        import openai

    if getattr(openai, "__prompthq_patch", False):
        logger.debug("Not patching. Already patched.")
        return

    if getattr(openai, "Completion", None):
        _patch_completion(openai)
    if getattr(openai, "ChatCompletion", None):
        _patch_chat_completion(openai)
    setattr(openai, "__prompthq_patch", True)

def serialize_result(obj: OpenAIObject):
    """For now, do the naive thing."""
    return obj.to_dict_recursive()
