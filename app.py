from flask import Flask, jsonify
from flask_socketio import SocketIO
import time
import random
import numpy as np

from stable_baselines3 import PPO
from simulation import SystemState, ProcessGenerator, simulate_step, Process

# 🔥 Load RL model (relative path)
rl_model = PPO.load("models/steward_ppo.zip")

# Modes: "RL", "RR", "DUMMY"
MODE = "RL"

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Shared objects
state = SystemState()
generator = ProcessGenerator(lam=1)  # reduced for stability

# ✅ API endpoint
@app.route("/api/status")
def get_status():
    return jsonify(state.snapshot())


# 🔥 Stress Test Endpoint
@app.route("/api/stress-test")
def stress_test():
    for _ in range(20):
        state.process_queue.append(
            Process(
                cpu=random.randint(10, 60),
                ram=random.randint(10, 60),
                burst_time=random.randint(1, 6)
            )
        )
    return {"status": "stress injected"}


# 🔄 Reset Endpoint
@app.route("/api/reset")
def reset():
    global state
    state = SystemState()
    return {"status": "reset done"}


# 🧠 Observation (MUST match RL training)
def get_observation(state):
    current = state.process_queue[0] if state.process_queue else None

    obs = [
        state.cpu_used,
        state.ram_used,
        len(state.process_queue),
        state.completed_count,

        # current process
        current.cpu if current else 0,
        current.ram if current else 0,
        current.burst_time if current else 0,

        # maybe queue stats
        sum(p.cpu for p in state.process_queue[:3]),
        sum(p.ram for p in state.process_queue[:3]),

        # padding / extras
        0, 0, 0
    ]

    return np.array(obs, dtype=np.float32)


# 🎮 Action selector
def get_action(obs):
    if MODE == "RL":
        action, _ = rl_model.predict(obs, deterministic=True)
        return int(action)

    elif MODE == "RR":
        return 0  # placeholder (you can upgrade later)

    return 0  # DUMMY


# 🔁 Main simulation loop (500ms)
def run_simulation():
    while True:
        obs = get_observation(state)
        action = get_action(obs)

        new_processes, reward, decision = simulate_step(state, generator, action)

        # 🧪 Logs
        if new_processes:
            print(f"[NEW] {new_processes}")

        print(f"[ACTION] {action} | [DECISION] {decision} | reward={reward}")
        print(f"[STATE] {state.snapshot()}")

        # 📡 Emit events
        socketio.emit("resource_update", state.snapshot())

        socketio.emit("decision_made", {
            "action": decision,
            "queue_length": len(state.process_queue)
        })

        socketio.emit("reward_update", {
            "reward": reward
        })

        time.sleep(0.5)


if __name__ == "__main__":
    socketio.start_background_task(run_simulation)
    socketio.run(app, host="0.0.0.0", port=5000)