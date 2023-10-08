import time

from rosnik.types.ai import AIFunctionMetadata, AIRequestStart

def track_request_start(func, request_payload: dict, metadata: AIFunctionMetadata):
    import pdb; pdb.set_trace()
    # TODO: Technically this works, but feels weird.
    ai_model = request_payload['model']
    ai_provider = metadata['ai_provider']
    ai_action = metadata['ai_action']
    # TODO: generate a journey ID
    event = AIRequestStart(journey_id="dog", sent_at=int(time.time()), _metadata={}, ai_model=ai_model, ai_provider=ai_provider, ai_action=ai_action, request_payload=request_payload)
    import pdb; pdb.set_trace()
    print(func)