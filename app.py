from flask import Flask, jsonify
from flask_socketio import SocketIO
import time
import random
import numpy as np
from flask_cors import CORS
from stable_baselines3 import PPO
from simulation import SystemState, ProcessGenerator, simulate_step, Process

# ── Load RL model ─────────────────────────────────────────────
rl_model = PPO.load("models/steward_ppo.zip", device="cpu")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ── Algorithms ────────────────────────────────────────────────
ALGO_NAMES = ["FCFS", "SJF", "RR", "Priority", "RL"]

def make_states():
    return {name: SystemState() for name in ALGO_NAMES}

def make_generators():
    return {name: ProcessGenerator(lam=0.5) for name in ALGO_NAMES}

states = make_states()
generators = make_generators()

# RR helpers
rr_index = {name: 0 for name in ALGO_NAMES}
rr_remain = {name: 0 for name in ALGO_NAMES}
RR_QUANTUM = 2


# ── RL Observation ────────────────────────────────────────────
def get_observation(state):
    processes = sorted(
        state.process_queue,
        key=lambda p: getattr(p, 'priority', 0),
        reverse=True
    )[:3]

    while len(processes) < 3:
        processes.append(Process(cpu=0, ram=0, burst_time=0))

    obs = [
        state.cpu_used,
        state.ram_used,
        len(state.process_queue)
    ]

    for p in processes:
        obs.extend([
            getattr(p, 'priority', 0),
            p.cpu,
            p.ram
        ])

    return np.array(obs, dtype=np.float32)


# ── Queue preparation ─────────────────────────────────────────
def prepare_queue(name, state):
    if name == "SJF":
        state.process_queue.sort(key=lambda p: p.burst_time)

    elif name == "Priority":
        state.process_queue.sort(
            key=lambda p: getattr(p, 'priority', 0),
            reverse=True
        )

    elif name == "RR":
        q = state.process_queue
        if q:
            if rr_remain[name] <= 0:
                rr_index[name] = (rr_index[name] + 1) % len(q)
                rr_remain[name] = RR_QUANTUM

            idx = rr_index[name] % len(q)
            state.process_queue = q[idx:] + q[:idx]
            rr_remain[name] -= 1


# ── Action selection ──────────────────────────────────────────
def choose_action(name, state):
    if name == "RL":
        obs = get_observation(state)
        action, _ = rl_model.predict(obs, deterministic=True)
        return int(action)

    return 0  # others always "schedule"


# ── Metrics ───────────────────────────────────────────────────
def compute_metrics(name, state):
    snap = state.snapshot()
    completed = getattr(state, "_completed_list", [])

    t = max(getattr(state, "time", 1), 1)

    avg_wait = (
        sum(p.wait_time for p in completed) / len(completed)
        if completed else 0
    )

    return {
        "name": name,
        "completed": state.completed_count,
        "queue": snap["queue_length"],
        "cpu": snap["cpu_used"],
        "ram": snap["ram_used"],
        "throughput": round(state.completed_count / t, 3),
        "avg_wait": round(avg_wait, 2),
    }


# ── API endpoints ─────────────────────────────────────────────
@app.route("/api/status")
def get_status():
    return jsonify({
        name: states[name].snapshot()
        for name in ALGO_NAMES
    })


@app.route("/api/stress-test")
def stress_test():
    for state in states.values():
        for _ in range(20):
            state.process_queue.append(
                Process(
                    cpu=random.randint(10, 60),
                    ram=random.randint(10, 60),
                    burst_time=random.randint(1, 6)
                )
            )
    return {"status": "stress injected"}


@app.route("/api/reset")
def reset():
    global states, generators, rr_index, rr_remain

    states = make_states()
    generators = make_generators()
    rr_index = {name: 0 for name in ALGO_NAMES}
    rr_remain = {name: 0 for name in ALGO_NAMES}

    return {"status": "reset done"}


# ── Main simulation loop ──────────────────────────────────────
def run_simulation():
    step = 0

    while True:
        step += 1
        all_metrics = []

        for name in ALGO_NAMES:
            state = states[name]
            gen = generators[name]

            # track time
            if not hasattr(state, "time"):
                state.time = 0
            state.time += 1

            prepare_queue(name, state)

            action = choose_action(name, state)

            new_procs, reward, decision, finished = simulate_step(
                state, gen, action, current_time=state.time
            )

            socketio.emit("resource_update", {
                "cpu_used": state.cpu_used,
                "ram_used": state.ram_used,
                "queue_length": len(state.process_queue)
            })


            # store completed processes
            if not hasattr(state, "_completed_list"):
                state._completed_list = []

            if finished:
                state._completed_list.append(finished)

            metrics = compute_metrics(name, state)
            all_metrics.append(metrics)
            

            if name == "RL":
                print(f"[RL] action={action} decision={decision} reward={reward:.2f}")
                socketio.emit("decision_made", {
                "pid": step,
                "action": action,
                "decision": decision
            })
                socketio.emit("reward_update", {
                    "reward": reward
                })
        # 🔥 DEBUG EMIT
        print(f"[EMIT] comparison_update | step={step} | algos={len(all_metrics)}")

        socketio.emit("comparison_update", {
            "step": step,
            "algos": all_metrics
        })
        

        # log summary
        print(
            f"[STEP {step}] " +
            " | ".join(
                f"{m['name']} done={m['completed']} q={m['queue']}"
                for m in all_metrics
            )
        )

        time.sleep(0.5)


# ── Run server ────────────────────────────────────────────────
if __name__ == "__main__":
    socketio.start_background_task(run_simulation)
    socketio.run(app, host="0.0.0.0", port=5000)