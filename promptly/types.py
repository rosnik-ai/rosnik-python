from typing import List, TypedDict


class PromptHqMetadata(TypedDict):
    platform: str
    action: str
    environment: str
    lang: str


class PromptHqEvent(TypedDict):
    request: dict
    response: dict
    function_fingerprint: List[str]
    start_time: int
    end_time: int
    _prompthq_metadata: PromptHqMetadata
