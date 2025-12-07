from dataclasses import dataclass

@dataclass
class Role():
    id:             int|None
    xp_threshold:   int
    server_id:      str
    cur_reward:     int

    def to_db(self):
        return (self.id, self.xp_threshold, self.server_id, self.cur_reward)
