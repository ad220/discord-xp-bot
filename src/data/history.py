from dataclasses import dataclass

@dataclass
class History():
    id              : int
    user_id         : int
    server_id       : int
    date            : int
    xp              : int
    msg             : int
    voice_uptime    : int
    currency        : int