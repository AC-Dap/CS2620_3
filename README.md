## Distributed System Simulation with Logical Clocks

### Overview
This project implements a simulation of a distributed system with three virtual machines that communicate via sockets. Each machine runs at a different clock speed, maintains a logical clock, processes messages from a network queue, and logs events. The simulation allows us to observe how different machine speeds and communication patterns affect clock synchronization and system behavior.

### Running Experiments
To run the full set of experiments:
```python run_experiments.py```

This will execute seven different experiments with varying parameters and save the results to timestamped directories.

### Analyzing Results
To analyze and visualize the experiment results:
```python analyze_results.py```

### Project Structure
├── model/
│   ├── __init__.py
│   ├── machine.py        # Virtual machine implementation
│   ├── message.py        # Message class definition
│   └── tests/            # Unit tests
├── run_experiments.py    # Script to run all experiments
├── visualize.py          # Script to analyze and visualize results
├── notebook.md           # Engineering notebook
└── README.md             # Project documentation