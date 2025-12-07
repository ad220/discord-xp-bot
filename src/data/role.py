from dataclasses import dataclass

@dataclass
class Role():
    id:             int|None
    xp_threshold:   int
    server_id:      str
    # cur_reward:     int
