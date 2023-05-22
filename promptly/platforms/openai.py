import typing

from promptly.utils import wrap_class_method


from openai.openai_object import OpenAIObject


def _patch_completion(openai):
    openai.Completion.create = wrap_class_method(
        openai.Completion, openai.Completion.create, "/v1/ingest/openai/completion"
    )


def _patch_chat_completion(openai):
    openai.ChatCompletion.create = wrap_class_method(
        openai.ChatCompletion, openai.ChatCompletion.create, "/v1/ingest/openai/chatcompletion"
    )


def _patch_openai(openai=None):
    if not openai:
        import openai

    if getattr(openai, "__promptly_patch", False):
        return

    print("Patching create")
    _patch_completion(openai)
    print("Patched create")
    setattr(openai, "__promptly_patch", True)


def serialize_result(obj: OpenAIObject):
    """For now, do the naive thing."""
    return obj.to_dict_recursive()
