import numpy as np
from env.process_queue import ProcessQueue

class FCFSScheduler:
    def __init__(self):
        self.max_cpu = 100
        self.max_ram = 100
        self.cpu_used = 0.0
        self.ram_used = 0.0
        self.completed = 0
        self.wait_times = []
        self.process_queue = ProcessQueue()
        self.tick = 0

    def step(self):
        if len(self.process_queue) > 0:
            process = self.process_queue.peek()
            if (self.cpu_used + process["cpu"] <= self.max_cpu and
                    self.ram_used + process["ram"] <= self.max_ram):
                self.cpu_used += process["cpu"]
                self.ram_used += process["ram"]
                self.process_queue.pop()
                self.completed += 1
                self.wait_times.append(self.tick)
            # no defer, no kill — strict FCFS, waits until front process can run

        if np.random.rand() < 0.6:
            self.process_queue.add_random()

        self.cpu_used = max(0, self.cpu_used - np.random.uniform(8, 15))
        self.ram_used = max(0, self.ram_used - np.random.uniform(6, 12))
        self.tick += 1

    def run(self, ticks=200):
        for _ in range(ticks):
            self.step()
        avg_wait = np.mean(self.wait_times) if self.wait_times else 0
        return {
            "completed": self.completed,
            "avg_wait_time": round(avg_wait, 2),
            "final_cpu": round(self.cpu_used, 2),
            "final_ram": round(self.ram_used, 2)
        }
        