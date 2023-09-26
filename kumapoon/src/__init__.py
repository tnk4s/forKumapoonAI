from gym.envs.registration import register

register(
    id='KumapoonGameEnv-v0',
    entry_point='src.main:KumapoonGameEnv'
)