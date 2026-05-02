import numpy as np
import random


# =========================
# PROCESS CLASS
# =========================
class Process:
    def __init__(self, cpu, ram, burst_time, priority=None, arrival_time=0):
        self.cpu = cpu
        self.ram = ram
        self.burst_time = burst_time
        self.remaining_burst = burst_time
        self.arrival_time = arrival_time
        self.priority = priority if priority is not None else random.randint(0, 3)
        self.wait_time = 0
        self.start_time = None
        self.finish_time = None

    def __repr__(self):
        return (f"P(cpu={self.cpu}, ram={self.ram}, burst={self.burst_time}, "
                f"remaining={self.remaining_burst}, priority={self.priority})")


# =========================
# PROCESS GENERATOR
# =========================
class ProcessGenerator:
    def __init__(self, lam=2):
        self.lam = lam

    def generate(self, current_time=0):
        num_arrivals = np.random.poisson(self.lam)
        return [
            Process(
                cpu=random.randint(10, 60),
                ram=random.randint(10, 60),
                burst_time=random.randint(1, 6),
                arrival_time=current_time
            )
            for _ in range(num_arrivals)
        ]


# =========================
# SYSTEM STATE
# =========================
class SystemState:
    def __init__(self):
        self.cpu_used = 0
        self.ram_used = 0
        self.process_queue = []
        self.completed = []
        self.time = 0
        self.last_decision = "none"

    @property
    def completed_count(self):
        return len(self.completed)

    def snapshot(self):
        return {
            "time": self.time,
            "cpu_used": self.cpu_used,
            "ram_used": self.ram_used,
            "queue_length": len(self.process_queue),
            "completed_count": self.completed_count,
            "last_decision": self.last_decision,
        }


# =========================
# METRICS
# =========================
def compute_metrics(state):
    done = state.completed
    t = max(state.time, 1)

    if not done:
        return {"throughput": 0.0, "avg_wait_time": 0.0, "completed": 0}

    return {
        "throughput": round(len(done) / t, 3),
        "avg_wait_time": round(sum(p.wait_time for p in done) / len(done), 2),
        "completed": len(done),
    }


# =========================
# SIMULATE STEP  (used by app.py)
# =========================
def simulate_step(state, generator=None, action=0, current_time=0):
    """
    action 0 = schedule
    action 1 = defer
    action 2 = kill

    Returns: new_processes, reward, decision, finished_process
    """
    finished_process = None
    new_processes = []

    if generator is not None:
        new_processes = generator.generate(current_time)
        state.process_queue.extend(new_processes)

    for p in state.process_queue:
        p.wait_time += 1

    reward = 0
    decision = "none"

    if state.process_queue:
        p = state.process_queue[0]

        if p.start_time is None:
            p.start_time = current_time

        if action == 0:  # schedule
            decision = "schedule"
            state.cpu_used = p.cpu
            state.ram_used = p.ram
            p.remaining_burst -= 1

            if p.remaining_burst <= 0:
                p.finish_time = current_time
                finished_process = p
                state.process_queue.pop(0)
                state.completed.append(p)   # fixed: was completed_count += 1
                reward += 1

        elif action == 1:  # defer
            decision = "defer"
            state.process_queue.append(state.process_queue.pop(0))
            reward -= 0.1

        elif action == 2:  # kill
            decision = "kill"
            finished_process = state.process_queue.pop(0)
            reward -= 0.5

    else:
        state.cpu_used = 0
        state.ram_used = 0

    if state.cpu_used > 100 or state.ram_used > 100:
        reward -= 1

    return new_processes, reward, decision, finished_process


# =========================
# BASE SCHEDULER
# =========================
class Scheduler:
    name = "Base"

    def __init__(self):
        self.state = SystemState()
        self.generator = ProcessGenerator()

    def select_process(self):
        raise NotImplementedError

    def _increment_wait(self):
        for p in self.state.process_queue:
            p.wait_time += 1

    def _complete(self, p):
        p.finish_time = self.state.time
        self.state.completed.append(p)
        self.state.cpu_used = p.cpu
        self.state.ram_used = p.ram

    def step(self):
        self.state.time += 1
        t = self.state.time

        arrivals = self.generator.generate(t)
        self.state.process_queue.extend(arrivals)
        self._increment_wait()

        queue = self.state.process_queue

        if not queue:
            self.state.cpu_used = 0
            self.state.ram_used = 0
            self.state.last_decision = "idle"
            return

        idx = self.select_process()
        p = queue[idx]

        if p.start_time is None:
            p.start_time = t

        self.state.cpu_used = p.cpu
        self.state.ram_used = p.ram
        self.state.last_decision = "schedule"

        p.remaining_burst -= 1

        if p.remaining_burst <= 0:
            self._complete(p)
            queue.pop(idx)

    def run(self, steps=100):
        for _ in range(steps):
            self.step()
        return compute_metrics(self.state)


# =========================
# FCFS
# =========================
class FCFSScheduler(Scheduler):
    name = "FCFS"

    def select_process(self):
        return 0


# =========================
# SJF
# =========================
class SJFScheduler(Scheduler):
    name = "SJF"

    def select_process(self):
        queue = self.state.process_queue
        return min(range(len(queue)), key=lambda i: queue[i].remaining_burst)


# =========================
# ROUND ROBIN
# =========================
class RoundRobinScheduler(Scheduler):
    name = "Round Robin"

    def __init__(self, quantum=2):
        super().__init__()
        self.quantum = quantum
        self._rr_index = 0
        self._rr_remain = 0

    def select_process(self):
        return self._rr_index

    def step(self):
        self.state.time += 1
        t = self.state.time

        arrivals = self.generator.generate(t)
        self.state.process_queue.extend(arrivals)
        self._increment_wait()

        queue = self.state.process_queue
        if not queue:
            self.state.cpu_used = 0
            self.state.ram_used = 0
            self.state.last_decision = "idle"
            self._rr_remain = 0
            return

        if self._rr_remain <= 0:
            self._rr_index = self._rr_index % len(queue)
            self._rr_remain = self.quantum

        idx = min(self._rr_index, len(queue) - 1)
        p = queue[idx]

        if p.start_time is None:
            p.start_time = t

        self.state.cpu_used = p.cpu
        self.state.ram_used = p.ram
        self.state.last_decision = "schedule"

        p.remaining_burst -= 1
        self._rr_remain -= 1

        if p.remaining_burst <= 0:
            self._complete(p)
            queue.pop(idx)
            self._rr_remain = 0
            self._rr_index = self._rr_index % max(1, len(queue))


# =========================
# PRIORITY
# =========================
class PriorityScheduler(Scheduler):
    name = "Priority"

    def select_process(self):
        queue = self.state.process_queue
        return max(range(len(queue)), key=lambda i: queue[i].priority)


# =========================
# RL HEURISTIC
# =========================
class RLScheduler(Scheduler):
    name = "RL"
    LOAD_THRESHOLD = 120
    KILL_THRESHOLD = 70
    KILL_QUEUE_MIN = 3

    def select_process(self):
        return 0

    def step(self):
        self.state.time += 1
        t = self.state.time

        arrivals = self.generator.generate(t)
        self.state.process_queue.extend(arrivals)
        self._increment_wait()

        queue = self.state.process_queue
        if not queue:
            self.state.cpu_used = 0
            self.state.ram_used = 0
            self.state.last_decision = "idle"
            return

        p = queue[0]
        load = p.cpu + p.ram + len(queue) * 2

        if (p.cpu > self.KILL_THRESHOLD
                and p.ram > self.KILL_THRESHOLD
                and len(queue) >= self.KILL_QUEUE_MIN):
            self._complete(p)
            queue.pop(0)
            self.state.last_decision = "kill"

        elif load > self.LOAD_THRESHOLD and len(queue) > 1:
            queue.append(queue.pop(0))
            self.state.last_decision = "defer"

        else:
            if p.start_time is None:
                p.start_time = t
            self.state.cpu_used = p.cpu
            self.state.ram_used = p.ram
            self.state.last_decision = "schedule"
            p.remaining_burst -= 1
            if p.remaining_burst <= 0:
                self._complete(p)
                queue.pop(0)


# =========================
# RUNNER
# =========================
def run_comparison(steps=200):
    schedulers = [
        FCFSScheduler(),
        SJFScheduler(),
        RoundRobinScheduler(quantum=2),
        PriorityScheduler(),
        RLScheduler(),
    ]

    print(f"{'Algorithm':<15} {'Completed':>10} {'Throughput':>12} {'Avg Wait':>10}")
    print("-" * 52)

    for sched in schedulers:
        metrics = sched.run(steps)
        print(
            f"{sched.name:<15}"
            f"{metrics['completed']:>10}"
            f"{metrics['throughput']:>12.3f}"
            f"{metrics['avg_wait_time']:>10.2f}"
        )


if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)
    run_comparison(steps=200)