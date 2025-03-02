from dataclasses import dataclass
from typing import Self


@dataclass
class Message:
    sender_id: str
    datetime: float

    def to_json(self):
        return {
            'sender_id': self.sender_id,
            'datetime': self.datetime
        }

    @classmethod
    def from_json(cls, json) -> Self:
        return cls(json['sender_id'], json['datetime'])
