from utils import wrap_class_method

def _patch_openai():
    import openai

    if getattr(openai, "__promptly_patch", False):
        return
    
    print("Patching create")
    openai.Completion.create = wrap_class_method(openai.Completion, openai.Completion.create)
    print("Patched create")
    setattr(openai, "__promptly_patch", True)