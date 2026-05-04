import numpy as np
from collections import deque

class ProcessQueue:
    def __init__(self):
        self.queue = deque()
        self._add_initial_processes(5)

    def _add_initial_processes(self, n):
        for _ in range(n):
            self.add_random()

    def add_random(self):
        process = {
            "pid": np.random.randint(1000, 9999),
            "cpu": np.random.uniform(5, 35),
            "ram": np.random.uniform(5, 30),
            "priority": np.random.randint(0, 4)  # 0=low, 1=normal, 2=high, 3=critical
        }
        self.queue.append(process)

    def peek(self):
        return self.queue[0] if self.queue else None

    def pop(self):
        return self.queue.popleft() if self.queue else None

    def defer(self):
        # move front process to back of queue
        if self.queue:
            self.queue.append(self.queue.popleft())

    def __len__(self):
        return len(self.queue)