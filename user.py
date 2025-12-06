from dataclasses import dataclass

@dataclass
class User():
    db_id:          int|None
    username:       str
    discord_id:     int
    server_id:      int
    xp:             int
    msg_count:      int
    voice_uptime:   int
    lastmsg_time:   int
    lastmsg_xp:     int
    currency:       int
    lastcur_date:   int
