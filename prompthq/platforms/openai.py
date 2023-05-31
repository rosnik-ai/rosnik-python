import logging

from prompthq.utils import wrap_class_method
from prompthq.types import PromptHqMetadata

from openai.openai_object import OpenAIObject

logger = logging.getLogger(__name__)

_OAI = "openai"
completion_metadata: PromptHqMetadata = {"platform": _OAI, "action": "completion"}
chat_completion_metadata: PromptHqMetadata = {"platform": _OAI, "action": "chatcompletion"}


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

    _patch_completion(openai)
    _patch_chat_completion(openai)
    setattr(openai, "__prompthq_patch", True)


def serialize_result(obj: OpenAIObject):
    """For now, do the naive thing."""
    return obj.to_dict_recursive()
