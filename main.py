from env.resource_env import ResourceEnv
from stable_baselines3.common.env_checker import check_env

env = ResourceEnv()
check_env(env)
print("Environment check passed.")
obs, _ = env.reset()
print(f"Initial obs: {obs}")