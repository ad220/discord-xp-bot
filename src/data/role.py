from dataclasses import dataclass

@dataclass
class Role():
    id:             int|None
    server_id:      str
    xp_threshold:   int
    cur_reward:     int
