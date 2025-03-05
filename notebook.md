### 3/5/2025

- After discussing in class, revert the revert of logical clock increments. We realized although incrementing by seconds makes sense, it doesn't actually have the property of causal ordering.

### 3/4/2025

- Caught a bug where machines are only listening for messages from one neighbor! After fixing, we now see experiments where the slower machine becomes backlogged in its network queue, being too slow to process messages from the faster machine. This is a good sign that the system is working as intended.

- Added experiment where add more weight to broadcasts, to see how important broadcasts are to maintaining clock sync. Initial results seem to be that there isn't much difference; perhaps since messages are being sent around by all the machines, there isn't a long period where a machine is not receiving messages.

- Thought about timezones a bit; what is the standardized way to handle them? Decided to do everything in UTC time, and convert to local time when displaying to the user. This way, we don't have to worry about time zones when doing computations on timestamps.

- Changed the logical clock to increment by the number of seconds passed, not number of events. This allows us to compare the logical clock against the system clock, and get a more meaningful definition of clock drift.

### 3/3/2025

- Create a set of experiments with different parameters to test the Lamport logical clock implementation:
  - Experiment 1: High clock variation (speeds 1-6), high internal event probability
  - Experiment 2: Low clock variation (speeds 4-6), high internal event probability
  - Experiment 3: High clock variation, low internal event probability
  - Experiment 4: Low clock variation, low internal event probability

- Each experiment runs for 60 seconds (with experiment one also run an extra time for 120 seconds) and involves 3 machines communicating via sockets
- Machines operate at different speeds based on the clock variation parameter
- Internal event probability affects how often machines perform internal events vs. sending messages

- The visualizations show logical clock progression, event type distribution, message queue sizes, and clock drift analysis for each experiment, helping us understand how different parameters affect system behavior.

- Added code to run experiments and visualize their results. Initial results show that the clock behavior is very balanced, despite different clock speeds. The distribution of events are slightly different, but nothing too concerning.

### 3/1/2025

- Created the rough layout of the machine. Have not tested; setup is still in progress.

- Thought about what message format we should pass from client to server. We likely want to pass multiple fields for debugging purposes, even though we technically just want to send timestamps. As such, parsing + sending a JSON object seems like a good idea. We can separate messages with newlines.
