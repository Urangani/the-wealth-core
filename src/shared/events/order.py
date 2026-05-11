from typing import Literal

from .base import BaseEvent


class OrderSubmittedEvent(BaseEvent):
    event_type: Literal["order.submitted"] = "order.submitted"
    payload: dict
