import numpy as np
import random
import time

class Process:
    def __init__(self, cpu, ram, burst_time):
        self.cpu = cpu
        self.ram = ram
        self.burst_time = burst_time
        self.wait_time = 0

    def __repr__(self):
        return f"P(cpu={self.cpu}, ram={self.ram}, time={self.burst_time})"


class ProcessGenerator:
    def __init__(self, lam=2):
        self.lam = lam  # avg arrivals per step

    def generate(self):
        num_arrivals = np.random.poisson(self.lam)
        processes = []

        for _ in range(num_arrivals):
            p = Process(
                cpu=random.randint(10, 60),
                ram=random.randint(10, 60),
                burst_time=random.randint(1, 6)
            )
            processes.append(p)

        return processes


class SystemState:
    def __init__(self):
        self.cpu_used = 0
        self.ram_used = 0
        self.process_queue = []
        self.completed_count = 0

    def snapshot(self):
        return {
            "cpu_used": self.cpu_used,
            "ram_used": self.ram_used,
            "queue_length": len(self.process_queue),
            "completed_count": self.completed_count
        }


# 🔧 SIMPLE STEP (no RL yet)
def simulate_step(state, generator, action=0):
    # 1. Generate new processes
    new_processes = generator.generate()
    state.process_queue.extend(new_processes)

    reward = 0
    decision = "none"

    if state.process_queue:
        p = state.process_queue[0]

        if action == 0:  # schedule
            decision = "schedule"
            state.cpu_used = p.cpu
            state.ram_used = p.ram
            p.burst_time -= 1

            if p.burst_time <= 0:
                state.process_queue.pop(0)
                state.completed_count += 1
                reward += 1

        elif action == 1:  # defer
            decision = "defer"
            state.process_queue.append(state.process_queue.pop(0))
            reward -= 0.1

        elif action == 2:  # kill
            decision = "kill"
            state.process_queue.pop(0)
            reward -= 0.5
    else:
        state.cpu_used = 0
        state.ram_used = 0

    # overload penalty
    if state.cpu_used > 100 or state.ram_used > 100:
        reward -= 1

    return new_processes, reward, decision