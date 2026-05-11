from typing import Literal

from .base import BaseEvent


class SignalGeneratedEvent(BaseEvent):
    event_type: Literal["signal.generated"] = "signal.generated"
    payload: dict
