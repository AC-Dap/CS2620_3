import threading
import time
import random
import json
from datetime import datetime, UTC
from queue import Queue
from model.message import Message

class Machine:
    def __init__(self, id, sockets, neighbors, log_file, speed, internal_event_probs):
        """
        Initialize a virtual machine.
        :param id: The id of this machine.
        :param sockets: A list of sockets that this machine will listen for messages over.
        :param neighbors: A list of sockets corresponding to the other machines in the network.
        :param log_file: The filepath to this machine's log file.
        :param speed: How many instructions this machine can execute per second.
        """
        self.id = id
        self.sockets = sockets
        self.neighbors = neighbors
        self.log_file = log_file
        self.speed = speed
        self.internal_event_probs = internal_event_probs

        # Initialize the logical clock to 0
        self.internal_clock = 0

        # Our machine will read from this queue
        # We have separate threads (not rate limited) for each listening socket that writes to this queue
        self.network_queue = Queue()
        self.network_threads = []

    def log_event(self, event, extra_text=""):
        """
        Log an event to this machine's log file.
        Prints the format [event]: [system time] [logical clock] [extra_text(optional)]
        :param event: The event to log.
        :param extra_text: Optional extra text to log.
        """
        with open(self.log_file, 'a') as f:
            system_time = datetime.now(UTC).time()
            f.write(f'[{event}]: {system_time} {self.internal_clock} {extra_text}\n')

    def start_network_threads(self):
        """
        Start network listening thread
        """
        for socket in self.sockets:
            thread = threading.Thread(target=self.listen_to_socket, args=(socket,))
            thread.daemon = True
            thread.start()
            self.network_threads.append(thread)

    def listen_to_socket(self, socket):
        """
        Listen to the network for messages.
        Any incoming messages will be added to the network queue.
        """
        buffer = ''
        while True:
            # Receive a message from the network.
            try:
                data = socket.recv(1024)
                if not data:  # Connection closed by the other side
                    print(f"[{self.id}] Connection closed by peer")
                    break
                buffer += data.decode('utf-8')
            except Exception as e:
                print(f"[{self.id}] Error received from socket: {e}")
                break

            # Split messages by newline
            next_newline = buffer.find('\n')
            while next_newline != -1:
                message_json = buffer[:next_newline]
                buffer = buffer[next_newline + 1:]

                try:
                    # Parse the message
                    message = Message.from_json(json.loads(message_json))

                    # Add the message to the network queue.
                    self.network_queue.put(message)
                except json.JSONDecodeError:
                    print(f"[{self.id}] Invalid JSON received: {message_json}")
                except Exception as e:
                    print(f"[{self.id}] Error processing message: {e}")

                # Find next message
                next_newline = buffer.find('\n')

    def run(self, stop_event=None):
        """
        Run the machine.

        :param stop_event: Threading event to signal when to stop the machine
        """

        while not (stop_event and stop_event.is_set()):
            # See if there is a pending message
            if self.network_queue.empty():
                rng = random.randint(0, 10)
                send_a_prob = self.internal_event_probs[0]
                send_b_prob = self.internal_event_probs[1]
                send_ab_prob = self.internal_event_probs[2]

                # Create message to be sent
                message = Message(self.id, self.internal_clock)
                message_json = json.dumps(message.to_json()).encode('utf-8') + b'\n'

                # Only send if we're still running
                if not (stop_event and stop_event.is_set()):
                    try:
                        if rng in send_a_prob:
                            # Send to neighbor 1
                            self.neighbors[0].send(message_json)
                            self.log_event('send', 'A')
                        elif rng in send_b_prob:
                            # Send to neighbor 2
                            self.neighbors[1].send(message_json)
                            self.log_event('send', 'B')
                        elif rng in send_ab_prob:
                            # Send to both neighbors
                            self.neighbors[0].send(message_json)
                            self.neighbors[1].send(message_json)
                            self.log_event('send', 'AB')
                        else:
                            self.log_event('idle')
                    except OSError:
                        # Socket might be closed, exit gracefully
                        break
            else:
                message: Message = self.network_queue.get()

                # Update logical clock according to Lamport's rule:
                # Take max of local clock and received clock, then increment
                self.internal_clock = max(self.internal_clock, message.datetime)

                self.log_event('recv', f"Queued Messages: {self.network_queue.qsize()}")

            # Increment logical clock for new event
            self.internal_clock += 1

            time.sleep(1 / self.speed)
