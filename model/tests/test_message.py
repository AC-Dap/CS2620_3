import unittest
from model.message import Message

class TestMessage(unittest.TestCase):
    def test_message_to_json(self):
        message = Message('sender', 123)
        json = message.to_json()
        self.assertEqual(json, {'sender_id': 'sender', 'datetime': 123})

    def test_message_from_json(self):
        json = {'sender_id': 'sender', 'datetime': 123}
        message = Message.from_json(json)
        self.assertEqual(message.sender_id, 'sender')
        self.assertEqual(message.datetime, 123)
