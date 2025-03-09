import sqlite3
from discord.enums import ChannelType

import cache

DB_PATH = 'data/data.db'

class Database:
    def __init__(self):
        self.con = sqlite3.connect(DB_PATH)
        self.cur = self.con.cursor()

    
    def __del__(self):
        self.con.close()


    def create_tables(self) -> None: 
        self.cur.execute('CREATE TABLE IF NOT EXISTS servers (id INTEGER PRIMARY KEY, name TEXT, xprate_msg INTEGER DEFAULT 1, xprate_voice INTEGER DEFAULT 1, mod_role INTEGER DEFAULT 0)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, discord_id INTEGER, server_id INTEGER, xp INTEGER DEFAULT 0, msg_count INTEGER DEFAULT 0, voice_uptime INTEGER DEFAULT 0)') 
        self.cur.execute('CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY, xp_threshold INTEGER, server_id INTEGER)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, type INTEGER, server_id INTEGER)')
        self.con.commit()


    def add_server(self, server_id: int, server_name: str) -> None:
        self.cur.execute('INSERT INTO servers(id, name) VALUES (?, ?)', (server_id, server_name))
        self.con.commit()


    def rm_server(self, server_id: int) -> None:
        self.cur.execute('DELETE FROM servers WHERE id = ?', (server_id,))
        self.cur.execute('DELETE FROM users WHERE server_id = ?', (server_id,))
        self.cur.execute('DELETE FROM roles WHERE server_id = ?', (server_id,))
        self.cur.execute('DELETE FROM channels WHERE server_id = ?', (server_id,))
        self.con.commit()

    def get_servers(self) -> list[int]:
        self.cur.execute('SELECT id FROM servers')
        return [server_id for (server_id,) in self.cur.fetchall()]


    def init_users(self, server_id: int, users: list[tuple[str, int]]) -> None:
        self.cur.executemany('INSERT INTO users(username, discord_id, server_id) VALUES (?, ?, ?)', [(username, discord_id, server_id) for (username, discord_id) in users])
        self.con.commit()


    def add_user(self, server_id: int, user_id: int, username: str, ) -> None:
        self.cur.execute('INSERT INTO users(username, discord_id, server_id) VALUES (?, ?, ?)', (username, user_id, server_id))
        self.con.commit()


    def rm_user(self, server_id: int, user_id: int) -> None:
        self.cur.execute('DELETE FROM users WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        self.con.commit()


    def set_role(self, server_id: int, role_id: int, xp_threshold: int) -> None:
        # check if role already exists
        self.cur.execute('SELECT * FROM roles WHERE id = ?', (role_id,))
        if self.cur.fetchone():
            # update xp_threshold value
            self.cur.execute('UPDATE roles SET xp_threshold = ? WHERE id = ?', (xp_threshold, role_id))
        else:
            self.cur.execute('INSERT INTO roles (id, xp_threshold, server_id) VALUES (?, ?, ?)', (role_id, xp_threshold, server_id))
        self.con.commit()


    def rm_role(self, role_id: int) -> None:
        self.cur.execute('DELETE FROM roles WHERE id = ?', (role_id,))
        self.con.commit()


    def add_channel(self, server_id: int, channel_id: int, channel_type: int) -> None:
        self.cur.execute('INSERT INTO channels (id, type, server_id) VALUES (?, ?, ?)', (channel_id, channel_type, server_id))
        self.con.commit()


    def rm_channel(self, channel_id: int) -> None:
        self.cur.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
        self.con.commit()


    def get_server_config(self, server_id: int) -> cache.ServerConfig:
        self.cur.execute('SELECT * FROM servers WHERE id = ?', (server_id,))
        guild_id, name, rate_txt, rate_voice, mod_role = self.cur.fetchone()

        self.cur.execute('SELECT id, xp_threshold FROM roles WHERE server_id = ? ORDER BY xp_threshold ASC', (server_id,))
        roles = self.cur.fetchall()

        channels = {}
        self.cur.execute('SELECT id FROM channels WHERE server_id = ? AND type = ?', (server_id, ChannelType.text.value))
        channels['text'] = [channel[0] for channel in self.cur.fetchall()]

        self.cur.execute('SELECT id FROM channels WHERE server_id = ? AND type = ?', (server_id, ChannelType.voice.value))
        channels['voice'] = [channel[0] for channel in self.cur.fetchall()]

        return cache.ServerConfig(guild_id,name, rate_txt, rate_voice, mod_role, roles, channels)
    

    def set_xp_rate_text(self, server_id: int, xp_rate: int) -> int:
        self.cur.execute('UPDATE servers SET xprate_msg = ? WHERE id = ?', (xp_rate, server_id))
        self.con.commit()

    
    def set_xp_rate_voice(self, server_id: int, xp_rate: int) -> None:
        self.cur.execute('UPDATE servers SET xprate_voice = ? WHERE id = ?', (xp_rate, server_id))
        self.con.commit()

    def set_mod_role(self, server_id: int, role_id: int) -> None:
        self.cur.execute('UPDATE servers SET mod_role = ? WHERE id = ?', (role_id, server_id))
        self.con.commit()


    def get_user_xp(self, server_id: int, user_id: int) -> int:
        self.cur.execute('SELECT xp FROM users WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        return self.cur.fetchone()[0]

    def set_user_xp(self, server_id: int, user_id: int, xp: int) -> None:
        self.cur.execute('UPDATE users SET xp = ? WHERE server_id = ? AND discord_id = ?', (xp, server_id, user_id))
        self.con.commit()
    
    def add_user_xp(self, server_id: int, user_id: int, xp: int) -> int:
        self.cur.execute('UPDATE users SET xp = xp + ? WHERE server_id = ? AND discord_id = ?', (xp, server_id, user_id))
        self.con.commit()
        self.cur.execute('SELECT xp FROM users WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        return self.cur.fetchone()[0]



    def get_user_msg_count(self, server_id: int, user_id: int) -> int:
        self.cur.execute('SELECT msg_count FROM users WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        return self.cur.fetchone()[0]
    
    def set_user_msg_count(self, server_id: int, user_id: int, msg_count: int) -> None:
        self.cur.execute('UPDATE users SET msg_count = ? WHERE server_id = ? AND discord_id = ?', (msg_count, server_id, user_id))
        self.con.commit()

    def add_user_msg_count(self, server_id: int, user_id: int, n_msg: int = 1) -> None:
        self.cur.execute('UPDATE users SET msg_count = msg_count + ? WHERE server_id = ? AND discord_id = ?', (n_msg, server_id, user_id))
        self.con.commit()


    def get_user_voice_uptime(self, server_id: int, user_id: int) -> int:
        self.cur.execute('SELECT voice_uptime FROM users WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        return self.cur.fetchone()[0]
    
    def set_user_voice_uptime(self, server_id: int, user_id: int, voice_uptime: int) -> None:
        self.cur.execute('UPDATE users SET voice_uptime = ? WHERE server_id = ? AND discord_id = ?', (voice_uptime, server_id, user_id))
        self.con.commit()
    
    def add_user_voice_uptime(self, server_id: int, user_id: int, n_min: int) -> None:
        self.cur.execute('UPDATE users SET voice_uptime = voice_uptime + ? WHERE server_id = ? AND discord_id = ?', (n_min, server_id, user_id))
        self.con.commit()


    def get_user(self, server_id, user_id: int) -> tuple:
        self.cur.execute('SELECT username, xp, msg_count, voice_uptime FROM users WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        return self.cur.fetchone()

    def get_users(self, server_id: int) -> list[tuple]:
        self.cur.execute('SELECT username, discord_id, xp, msg_count, voice_uptime FROM users WHERE server_id = ? ORDER BY xp DESC', (server_id,))
        return self.cur.fetchmany(10)
