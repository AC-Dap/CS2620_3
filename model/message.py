from dataclasses import dataclass

@dataclass
class Message:
    sender_id: str
    datetime: float

    def to_json(self):
        return {
            'sender_id': self.sender_id,
            'datetime': self.datetime
        }
