import os
import socket
import multiprocessing
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

def start_machine(id, port, neighbor_ports, log_file, speed, internal_event_probs, stop_event):
    """
    Start a machine in the distributed system.

    Parameters:
    - port: Port number for the machine to listen on
    - neighbor_ports: List of port numbers for the machine's neighbors
    - log_file: File to log machine events to
    - speed: Speed of the machine's internal clock
    - internal_event_probs: List of probabilities for internal events
    """
    # Create a socket for the machine
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of address
    server.bind(('localhost', port))
    server.listen(5)

    # Sleep a bit to allow for neighbor sockets to be created
    time.sleep(0.5)

    # Connect to the neighbors
    connections = []
    for neighbor_port in neighbor_ports:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', neighbor_port))
        connections.append(client)

    # Accept the incoming connection
    accepted_connections = []
    for _ in range(len(neighbor_ports)):
        conn, addr = server.accept()
        accepted_connections.append(conn)

    # Create and start the machine
    machine = Machine(f"Machine_{id}", accepted_connections, connections, log_file, speed, internal_event_probs)
    machine.start_network_threads()
    machine.run(stop_event)

    # Clean up
    for conn in connections:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
    server.close()

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
    stop_event = multiprocessing.Event()
    for i in range(3):
        log_file = f"{exp_dir}/machine_{i}.log"
        machine = multiprocessing.Process(target=start_machine, args=(
            i, 5000 + i, [5000 + j for j in range(3) if j != i],
            log_file, speeds[i], internal_event_probs, stop_event)
        )
        machine.start()
        machines.append(machine)

    # Run for specified duration
    print(f"Experiment running for {duration} seconds...")
    time.sleep(duration)

    # Signal machines to stop
    stop_event.set()

    # Wait for machines to terminate (with timeout)
    for m in machines:
        m.join(timeout=1.0)

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
