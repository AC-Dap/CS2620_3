import os
import socket
import threading
import time
import random
from datetime import datetime, UTC
from model.machine import Machine

def create_experiment_directory():
    """Create a directory for the experiment results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"experiment_{timestamp}"
    os.makedirs(dir_name, exist_ok=True)
    return dir_name

def run_experiment(duration=60, clock_variation="high", internal_event_prob="high"):
    """
    Run a distributed system experiment.

    Parameters:
    - duration: Duration of the experiment in seconds
    - clock_variation: "high" (1-6) or "low" (4-6)
    - internal_event_prob: "high" (1-10) or "low" (1-5) or "weighted" (higher chance of broadcast)
    """
    # Create experiment directory
    exp_dir = create_experiment_directory()

    # Create sockets for the machines
    sockets = []
    for i in range(3):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of address
        server.bind(('localhost', 10000 + i))
        server.listen(5)
        sockets.append(server)

    # Accept connections
    connections = [[] for _ in range(3)]

    # Connect machines to each other
    for i in range(3):
        for j in range(3):
            if i != j:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(('localhost', 10000 + j))
                connections[i].append(client)

    # Accept the incoming connections
    accepted_connections = [[] for _ in range(3)]
    for i in range(3):
        for _ in range(2):  # Each machine connects to 2 others
            conn, addr = sockets[i].accept()
            accepted_connections[i].append(conn)

    # Determine clock speeds
    if clock_variation == "high":
        speeds = [random.randint(1, 6) for _ in range(3)]
    else:
        speeds = [random.randint(4, 6) for _ in range(3)]

    # Adjust internal event probability
    if internal_event_prob == "low":
        internal_event_probs = ([1], [2], [3])
    elif internal_event_prob == "high":
        internal_event_probs = ([1, 2], [3, 4], [5, 6])
    elif internal_event_prob == "weighted":
        internal_event_probs = ([1], [2], [3, 4, 5])
    else:
        raise ValueError("Invalid internal event probability")

    # Create and start machines
    machines = []
    for i in range(3):
        log_file = f"{exp_dir}/machine_{i}.log"
        machine = Machine(f"Machine_{i}", accepted_connections[i], connections[i], log_file, speeds[i], internal_event_probs)
        machine.start_network_threads()
        machines.append(machine)

    # Create a stop event to signal threads to terminate
    stop_event = threading.Event()

    # Start machine threads
    machine_threads = []
    start_time = datetime.now(UTC).timestamp()
    for machine in machines:
        thread = threading.Thread(target=machine.run, args=(stop_event, start_time))
        thread.daemon = True
        thread.start()
        machine_threads.append(thread)

    # Run for specified duration
    print(f"Experiment running for {duration} seconds...")
    time.sleep(duration)

    # Signal threads to stop
    stop_event.set()

    # Wait for threads to terminate (with timeout)
    for thread in machine_threads:
        thread.join(timeout=1.0)

    # Clean up - first shutdown the sockets to signal network threads to exit
    for conn_list in connections:
        for conn in conn_list:
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except OSError:
                pass  # Socket might already be closed

    for conn_list in accepted_connections:
        for conn in conn_list:
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except OSError:
                pass  # Socket might already be closed

    for server in sockets:
        try:
            server.close()
        except OSError:
            pass  # Socket might already be closed

    # Give network threads a moment to exit
    time.sleep(0.5)

    # Save experiment parameters
    with open(f"{exp_dir}/parameters.txt", "w") as f:
        f.write(f"Duration: {duration} seconds\n")
        f.write(f"Clock variation: {clock_variation}\n")
        f.write(f"Internal event probability: {internal_event_prob}\n")
        f.write(f"Machine speeds: {speeds}\n")

    print(f"Experiment completed. Results saved in {exp_dir}")
    return exp_dir

def main():
    # Run experiments with different parameters
    print("Running experiment 1: High clock variation, high internal event probability")
    run_experiment(duration=60, clock_variation="high", internal_event_prob="high")

    print("Running experiment 2: Low clock variation, high internal event probability")
    run_experiment(duration=60, clock_variation="low", internal_event_prob="high")

    print("Running experiment 3: High clock variation, low internal event probability")
    run_experiment(duration=60, clock_variation="high", internal_event_prob="low")

    print("Running experiment 4: Low clock variation, low internal event probability")
    run_experiment(duration=60, clock_variation="low", internal_event_prob="low")

    print("Running experiment 5: High clock variation, high internal event probability (longer duration)")
    run_experiment(duration=120, clock_variation="high", internal_event_prob="high")

    print("Running experiment 6: High clock variation, weighted internal event probability")
    run_experiment(duration=60, clock_variation="high", internal_event_prob="weighted")

    print("Running experiment 7: Low clock variation, weighted internal event probability")
    run_experiment(duration=60, clock_variation="low", internal_event_prob="weighted")

if __name__ == "__main__":
    main()
