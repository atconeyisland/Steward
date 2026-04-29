from flask import Flask, jsonify
from flask_socketio import SocketIO
import time

from simulation import SystemState, ProcessGenerator, simulate_step

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Shared objects
state = SystemState()
generator = ProcessGenerator(lam=2)

MODE = "DUMMY"  # later: "RL" or "RR"


# ✅ API endpoint
@app.route("/api/status")
def get_status():
    return jsonify(state.snapshot())


# 🧠 Build observation (VERY IMPORTANT for RL later)
def get_observation(state):
    return [
        state.cpu_used,
        state.ram_used,
        len(state.process_queue),
        state.completed_count
    ]


# 🎮 Action selector (temporary)
def get_action(obs):
    if MODE == "DUMMY":
        return 0  # always schedule

    # future:
    # if MODE == "RL":
    #     return rl_model.predict(obs)[0]
    # elif MODE == "RR":
    #     return round_robin_policy()

    return 0


# 🔁 Background simulation loop
def run_simulation():
    while True:
        # 🧠 build observation
        obs = [
            state.cpu_used,
            state.ram_used,
            len(state.process_queue),
            state.completed_count
        ]

        # 🎮 temporary action (Day 1)
        action = 0  # always schedule

        # 🔁 step simulation
        new_processes, reward, decision = simulate_step(state, generator, action)

        # 🧪 logs
        if new_processes:
            print(f"[NEW] {new_processes}")

        print(f"[DECISION] {decision} | reward={reward}")
        print(f"[STATE] {state.snapshot()}")

        # 📡 emit events
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