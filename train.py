import os
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from env.resource_env import ResourceEnv

class RewardLoggerCallback(BaseCallback):
    def __init__(self):
        super().__init__()
        self.episode_rewards = []
        self.current_reward = 0.0

    def _on_step(self):
        self.current_reward += self.locals["rewards"][0]
        if self.locals["dones"][0]:
            self.episode_rewards.append(self.current_reward)
            self.current_reward = 0.0
        return True

def train():
    env = ResourceEnv()
    callback = RewardLoggerCallback()

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        clip_range=0.2,
    )

    print("Training started...")
    model.learn(total_timesteps=200_000, callback=callback)
    print("Training complete.")

    os.makedirs("models", exist_ok=True)
    model.save("models/steward_ppo")
    print("Model saved to models/steward_ppo.zip")

    plot_rewards(callback.episode_rewards)

def plot_rewards(rewards):
    if not rewards:
        print("No episode rewards to plot.")
        return

    os.makedirs("assets", exist_ok=True)

    # smooth with rolling average
    window = 20
    smoothed = np.convolve(rewards, np.ones(window) / window, mode="valid")

    plt.figure(figsize=(10, 5))
    plt.plot(rewards, alpha=0.3, color="steelblue", label="Raw reward")
    plt.plot(range(window - 1, len(rewards)), smoothed, color="steelblue", linewidth=2, label=f"Smoothed (window={window})")
    plt.xlabel("Episode")
    plt.ylabel("Cumulative Reward")
    plt.title("Arbiter — PPO Training Reward Curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig("assets/reward_curve.png", dpi=150)
    plt.show()
    print("Reward curve saved to assets/reward_curve.png")

if __name__ == "__main__":
    train()