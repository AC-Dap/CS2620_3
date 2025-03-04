### 3/4/2025

- Thought about timezones a bit; what is the standardized way to handle them? Decided to do everything in UTC time, and convert to local time when displaying to the user. This way, we don't have to worry about time zones when doing computations on timestamps.

- Changed the logical clock to increment by the number of seconds passed, not number of events. This allows us to compare the logical clock against the system clock, and get a more meaningful definition of clock drift.

### 3/3/2025

- Added code to run experiments and visualize their results. Initial results show that the clock behavior is very balanced, despite different clock speeds. The distribution of events are slightly different, but nothing too concerning.

### 3/1/2025

- Created the rough layout of the machine. Have not tested; setup is still in progress.

- Thought about what message format we should pass from client to server. We likely want to pass multiple fields for debugging purposes, even though we technically just want to send timestamps. As such, parsing + sending a JSON object seems like a good idea. We can separate messages with newlines.
