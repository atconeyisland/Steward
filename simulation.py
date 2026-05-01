import numpy as np
import random


# =========================
# PROCESS CLASS
# =========================
class Process:
    def __init__(self, cpu, ram, burst_time):
        self.cpu = cpu
        self.ram = ram
        self.burst_time = burst_time

        # metrics
        self.wait_time = 0
        self.start_time = None
        self.finish_time = None

    def __repr__(self):
        return f"P(cpu={self.cpu}, ram={self.ram}, time={self.burst_time})"


# =========================
# PROCESS GENERATOR
# =========================
class ProcessGenerator:
    def __init__(self, lam=2):
        self.lam = lam  # average arrivals per step

    def generate(self):
        num_arrivals = np.random.poisson(self.lam)
        processes = []

        for _ in range(num_arrivals):
            processes.append(Process(
                cpu=random.randint(10, 60),
                ram=random.randint(10, 60),
                burst_time=random.randint(1, 6)
            ))

        return processes


# =========================
# SYSTEM STATE
# =========================
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


# =========================
# MAIN SIMULATION STEP
# =========================
def simulate_step(state, generator=None, action=0, current_time=0):
    """
    Performs one simulation step.

    Returns:
        new_processes
        reward
        decision (string)
        finished_process (or None)
    """

    finished_process = None
    new_processes = []

    # -------------------------
    # 1. Generate new processes
    # -------------------------
    if generator is not None:
        new_processes = generator.generate()
        state.process_queue.extend(new_processes)

    # -------------------------
    # 2. Update wait time
    # -------------------------
    for p in state.process_queue:
        p.wait_time += 1

    reward = 0
    decision = "none"

    # -------------------------
    # 3. Scheduling decision
    # -------------------------
    if state.process_queue:
        p = state.process_queue[0]

        # set start time once
        if p.start_time is None:
            p.start_time = current_time

        if action == 0:  # schedule
            decision = "schedule"
            state.cpu_used = p.cpu
            state.ram_used = p.ram

            p.burst_time -= 1

            if p.burst_time <= 0:
                p.finish_time = current_time
                finished_process = p

                state.process_queue.pop(0)
                state.completed_count += 1
                reward += 1

        elif action == 1:  # defer
            decision = "defer"
            state.process_queue.append(state.process_queue.pop(0))
            reward -= 0.1

        elif action == 2:  # kill
            decision = "kill"
            finished_process = p

            state.process_queue.pop(0)
            reward -= 0.5

    else:
        state.cpu_used = 0
        state.ram_used = 0

    # -------------------------
    # 4. Overload penalty
    # -------------------------
    if state.cpu_used > 100 or state.ram_used > 100:
        reward -= 1

    return new_processes, reward, decision, finished_process


# =========================
# METRICS FUNCTION
# =========================
def compute_metrics(completed_processes, time_elapsed):
    """
    Returns throughput and average wait time
    """

    if len(completed_processes) == 0:
        return {
            "throughput": 0,
            "avg_wait_time": 0
        }

    throughput = len(completed_processes) / max(time_elapsed, 1)

    avg_wait = sum(p.wait_time for p in completed_processes) / len(completed_processes)

    return {
        "throughput": round(throughput, 2),
        "avg_wait_time": round(avg_wait, 2)
    }