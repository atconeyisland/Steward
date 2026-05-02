from flask import Flask, jsonify
from flask_socketio import SocketIO
import time
import random
import numpy as np

from stable_baselines3 import PPO
from simulation import SystemState, ProcessGenerator, simulate_step, Process

rl_model = PPO.load("models/steward_ppo.zip")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ── One state + generator per algorithm ──────────────────────────────────────
ALGO_NAMES = ["FCFS", "SJF", "RR", "Priority", "RL"]

def make_states():
    return {name: SystemState() for name in ALGO_NAMES}

def make_generators():
    return {name: ProcessGenerator(lam=0.3) for name in ALGO_NAMES}

states     = make_states()
generators = make_generators()

rr_index   = {name: 0 for name in ALGO_NAMES}   # used only by RR
rr_remain  = {name: 0 for name in ALGO_NAMES}
RR_QUANTUM = 2


# ── Action selectors ─────────────────────────────────────────────────────────
def get_observation(state):
    processes = sorted(state.process_queue,
                       key=lambda p: getattr(p, 'priority', 0), reverse=True)[:3]
    while len(processes) < 3:
        processes.append(Process(cpu=0, ram=0, burst_time=0))
    obs = [state.cpu_used, state.ram_used, len(state.process_queue)]
    for p in processes:
        obs.extend([getattr(p, 'priority', 0), p.cpu, p.ram])
    return np.array(obs, dtype=np.float32)


def prepare_queue(name, state):
    """Sort queue in-place before simulate_step picks index 0."""
    if name == "SJF":
        state.process_queue.sort(key=lambda p: p.burst_time)
    elif name == "Priority":
        state.process_queue.sort(key=lambda p: getattr(p, 'priority', 0), reverse=True)
    elif name == "RR":
        q = state.process_queue
        if q:
            if rr_remain[name] <= 0:
                rr_index[name]  = (rr_index[name] + 1) % len(q)
                rr_remain[name] = RR_QUANTUM
            # Rotate so chosen process is at front (simulate_step picks index 0)
            idx = rr_index[name] % len(q)
            state.process_queue = q[idx:] + q[:idx]
            rr_remain[name] -= 1


def choose_action(name, state):
    if name == "RL":
        obs = get_observation(state)
        action, _ = rl_model.predict(obs, deterministic=True)
        return int(action)
    return 0   # FCFS / SJF / RR / Priority all just schedule (queue already sorted)


# ── Metrics helper ────────────────────────────────────────────────────────────
def algo_metrics(name, state):
    snap = state.snapshot()
    done = state.completed_count
    t    = max(state.time if hasattr(state, 'time') else 1, 1)
    completed = getattr(state, '_completed_list', [])
    avg_wait  = (sum(p.wait_time for p in completed) / len(completed)
                 if completed else 0)
    return {
        "name":        name,
        "completed":   done,
        "queue":       snap["queue_length"],
        "cpu":         snap["cpu_used"],
        "ram":         snap["ram_used"],
        "throughput":  round(done / t, 3),
        "avg_wait":    round(avg_wait, 2),
    }


# ── API endpoints ─────────────────────────────────────────────────────────────
@app.route("/api/status")
def get_status():
    return jsonify({name: states[name].snapshot() for name in ALGO_NAMES})


@app.route("/api/stress-test")
def stress_test():
    for state in states.values():
        for _ in range(20):
            state.process_queue.append(
                Process(cpu=random.randint(10, 60),
                        ram=random.randint(10, 60),
                        burst_time=random.randint(1, 6))
            )
    return {"status": "stress injected"}


@app.route("/api/reset")
def reset():
    global states, generators, rr_index, rr_remain
    states     = make_states()
    generators = make_generators()
    rr_index   = {name: 0 for name in ALGO_NAMES}
    rr_remain  = {name: 0 for name in ALGO_NAMES}
    return {"status": "reset done"}


# ── Main loop ─────────────────────────────────────────────────────────────────
def run_simulation():
    step = 0
    while True:
        step += 1
        all_metrics = []

        for name in ALGO_NAMES:
            state = states[name]
            gen   = generators[name]

            # Track time manually (SystemState doesn't have it by default)
            if not hasattr(state, 'time'):
                state.time = 0
            state.time += 1

            # Sort / rotate queue before picking
            prepare_queue(name, state)

            action = choose_action(name, state)

            new_procs, reward, decision, finished = simulate_step(
                state, gen, action, current_time=state.time
            )

            # Keep completed list for avg_wait calculation
            if not hasattr(state, '_completed_list'):
                state._completed_list = []
            if finished:
                state._completed_list.append(finished)

            all_metrics.append(algo_metrics(name, state))

            if name == "RL":
                print(f"[RL] action={action} decision={decision} reward={reward:.2f}")

        # Single emit with all 5 algorithms' data
        socketio.emit("comparison_update", {
            "step":    step,
            "algos":   all_metrics,
        })

        print(f"[STEP {step}] " + " | ".join(
            f"{m['name']} done={m['completed']} q={m['queue']}" for m in all_metrics
        ))

        time.sleep(0.5)


if __name__ == "__main__":
    socketio.start_background_task(run_simulation)
    socketio.run(app, host="0.0.0.0", port=5000)