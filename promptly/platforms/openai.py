from promptly.utils import wrap_class_method


def _patch_completion(openai):
    openai.Completion.create = wrap_class_method(openai.Completion, openai.Completion.create)


def _patch_openai(openai=None):
    if not openai:
        import openai

    if getattr(openai, "__promptly_patch", False):
        return

    print("Patching create")
    _patch_completion(openai)
    print("Patched create")
    setattr(openai, "__promptly_patch", True)
