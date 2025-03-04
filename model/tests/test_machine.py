import queue
import unittest
import socket
from unittest.mock import patch, mock_open
from datetime import datetime
from model.machine import Machine
from model.message import Message

class TestMachine(unittest.TestCase):
    def test_log_event(self):
        with patch("builtins.open", mock_open()) as mock_file:
            test_time = datetime.now()
            with patch('model.machine.datetime', autospec=True) as mock_datetime:
                mock_datetime.now.return_value = test_time
                mock_datetime.fromtimestamp.return_value = test_time

                machine = Machine(0, None, [], 'test.log', 1)
                machine.log_event('test_event', 'extra_text')

                mock_file.assert_called_with('test.log', 'a')
                mock_file().write.assert_called_with(f'[test_event]: {test_time.time()} {test_time.time()} extra_text\n')

    def test_listen_to_network(self):
        test_messages = [
            b'{"sender_id": "sender", "datetime": 123}\n',
            b'{"sender_id": "sender2", "datetime": 456}\n',
            socket.error("Connection closed")
        ]

        with patch('socket.socket') as mock_socket:
            sock = mock_socket.return_value
            machine = Machine(0, sock, [], 'test.log', 1)

            # Set up mock socket
            sock.recv.side_effect = test_messages
            machine.start_network_threads()

            self.assertEqual(machine.network_queue.get(block=False), Message('sender', 123))
            self.assertEqual(machine.network_queue.get(block=False), Message('sender2', 456))
            with self.assertRaises(queue.Empty):
                machine.network_queue.get(block=False)
