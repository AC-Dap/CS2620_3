import threading
import time
import random
import json
from datetime import datetime, UTC
from queue import Queue
from model.message import Message

class Machine:
    def __init__(self, id, socket, neighbors, log_file, speed):
        """
        Initialize a virtual machine.
        :param id: The id of this machine.
        :param socket: An opened socket that this machine will listen for messages over.
        :param neighbors: A list of sockets corresponding to the other machines in the network.
        :param log_file: The filepath to this machine's log file.
        :param speed: How many instructions this machine can execute per second.
        """
        self.id = id
        self.socket = socket
        self.neighbors = neighbors
        self.log_file = log_file
        self.speed = speed

        # Initialize the internal clock. This is the number of milliseconds since the epoch.
        self.internal_clock = datetime.now().replace(tzinfo=UTC).timestamp()

        # Our machine will read from this queue
        # We have a separate thread (not rate limited) that reads from the socket and writes to this queue
        self.network_queue = Queue()

        # Start network listening thread
        self.network_thread = threading.Thread(target=self.listen_to_network)
        self.network_thread.start()

    def log_event(self, event, extra_text=""):
        """
        Log an event to this machine's log file.
        Prints the format [event]: [system time] [internal clock] [extra_text(optional)]
        :param event: The event to log.
        :param extra_text: Optional extra text to log.
        """
        with open(self.log_file, 'a') as f:
            system_time = datetime.now().time()
            internal_time = datetime.fromtimestamp(self.internal_clock, UTC).time()
            f.write(f'[{event}]: {system_time} {internal_time} {extra_text}\n')

    def listen_to_network(self):
        """
        Listen to the network for messages.
        Any incoming messages will be added to the network queue.
        """
        buffer = ''
        while True:
            # Receive a message from the network.
            buffer += self.socket.recv(1024).decode('utf-8')

            # Split messages by newline
            next_newline = buffer.find('\n')
            while next_newline != -1:
                message_json = buffer[:next_newline]
                buffer = buffer[next_newline + 1:]

                # Parse the message
                message = Message.from_json(json.loads(message_json))

                # Add the message to the network queue.
                self.network_queue.put(message)

                # Find next message
                next_newline = buffer.find('\n')

    def run(self):
        """
        Run the machine.
        """
        while True:
            # See if there is a pending message
            if self.network_queue.empty():
                rng = random.randint(1, 10)

                # Create message to be sent
                message = Message(self.id, self.internal_clock)
                message_json = json.dumps(message.to_json()).encode('utf-8') + b'\n'
                if rng == 1:
                    # Send to neighbor 1
                    self.neighbors[0].send(message_json)
                    self.log_event('send', 'A')
                elif rng == 2:
                    # Send to neighbor 2
                    self.neighbors[1].send(message_json)
                    self.log_event('send', 'B')
                elif rng == 3:
                    # Send to both neighbors
                    self.neighbors[0].send(message_json)
                    self.neighbors[1].send(message_json)
                    self.log_event('send', 'AB')
                else:
                    self.log_event('idle')
            else:
                message: Message = self.network_queue.get()

                # Update internal clock
                self.internal_clock = message.datetime

                self.log_event('recv', f"Queued Messages: {self.network_queue.qsize()}")

            time.sleep(1 / self.speed)
            self.internal_clock += 1 / self.speed
