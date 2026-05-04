import numpy as np
from env.process_queue import ProcessQueue

class SJFScheduler:
    def __init__(self):
        self.max_cpu = 100
        self.max_ram = 100
        self.cpu_used = 0.0
        self.ram_used = 0.0
        self.completed = 0
        self.wait_times = []
        self.process_queue = ProcessQueue()
        self.tick = 0

    def _get_shortest_job(self):
        if len(self.process_queue) == 0:
            return None
        processes = list(self.process_queue.queue)
        processes.sort(key=lambda p: p["cpu"])
        return processes[0]

    def _remove_process(self, pid):
        self.process_queue.queue = __import__('collections').deque(
            p for p in self.process_queue.queue if p["pid"] != pid
        )

    def step(self):
        process = self._get_shortest_job()
        if process:
            if (self.cpu_used + process["cpu"] <= self.max_cpu and
                    self.ram_used + process["ram"] <= self.max_ram):
                self.cpu_used += process["cpu"]
                self.ram_used += process["ram"]
                self._remove_process(process["pid"])
                self.completed += 1
                self.wait_times.append(self.tick)

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