### 3/1/2025

- Created the rough layout of the machine. Have not tested; setup is still in progress.

- Thought about what message format we should pass from client to server. We likely want to pass multiple fields for debugging purposes, even though we technically just want to send timestamps. As such, parsing + sending a JSON object seems like a good idea. We can separate messages with newlines.
