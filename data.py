import sqlite3

DB_PATH = 'data/data.db'

class Database:
    def __init__(self):
        self.con = sqlite3.connect(DB_PATH)
        self.cur = self.con.cursor()

    
    def __del__(self):
        self.con.close()


    def create_tables(self) -> None: 
        self.cur.execute('CREATE TABLE IF NOT EXISTS servers (id INTEGER PRIMARY KEY, name TEXT, xprate_msg INTEGER DEFAULT 1, xprate_voice INTEGER DEFAULT 1)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, discord_id INTEGER, server_id INTEGER, xp INTEGER DEFAULT 0, msg_count INTEGER DEFAULT 0, voice_uptime INTEGER DEFAULT 0)') 
        self.cur.execute('CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY, xp_threshold INTEGER, server_id INTEGER)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, type TEXT, server_id INTEGER)')
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


    def init_users(self, server_id: int, users: list[tuple[str, int]]) -> None:
        self.cur.executemany('INSERT INTO users(username, discord_id, server_id) VALUES (?, ?, ?)', [(username, discord_id, server_id) for (username, discord_id) in users])
        self.con.commit()


    def add_user(self, server_id: int, username: str, discord_id: int) -> None:
        self.cur.execute('INSERT INTO users(username, discord_id, server_id) VALUES (?, ?, ?)', (username, discord_id, server_id))
        self.con.commit()


    def rm_user(self, server_id: int, discord_id: int) -> None:
        self.cur.execute('DELETE FROM users WHERE server_id = ? AND discord_id = ?', (server_id, discord_id))
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


    def edit_channels(self, server_id: int, channels: list[tuple[int, str]]) -> None:
        self.cur.execute('DELETE FROM channels WHERE server_id = ?', (server_id,))
        self.cur.executemany('INSERT INTO channels VALUES (?, ?, ?)', [(channel_id, channel_type, server_id) for (channel_id, channel_type) in channels])
        self.con.commit()


    def get_server_config(self, server_id: int) -> dict:
        self.cur.execute('SELECT * FROM servers WHERE id = ?', (server_id,))
        id, name, rate_txt, rate_voice = self.cur.fetchone()
        server_config = {   
            'id': id,
            'name': name,
            'rate_txt': rate_txt,
            'rate_voice': rate_voice
        }

        self.cur.execute('SELECT id, xp_threshold FROM roles WHERE server_id = ?', (server_id,))
        server_config['roles'] = self.cur.fetchall()

        self.cur.execute('SELECT id FROM channels WHERE server_id = ? AND type = ?', (server_id, "text"))
        server_config['channels']['text'] = self.cur.fetchall()

        self.cur.execute('SELECT id FROM channels WHERE server_id = ? AND type = ?', (server_id, "voice"))
        server_config['channels']['voice'] = self.cur.fetchall()

        return server_config
    

    def set_xp_rate_text(self, server_id: int, xp_rate: int) -> int:
        self.cur.execute('UPDATE servers SET xprate_msg = ? WHERE id = ?', (xp_rate, server_id))
        self.con.commit()

    
    def set_xp_rate_voice(self, server_id: int, xp_rate: int) -> None:
        self.cur.execute('UPDATE servers SET xprate_voice = ? WHERE id = ?', (xp_rate, server_id))
        self.con.commit()


    def get_user_xp(self, server_id: int, discord_id: int) -> int:
        self.cur.execute('SELECT xp FROM users WHERE server_id = ? AND discord_id = ?', (server_id, discord_id))
        return self.cur.fetchone()[0]


    def set_user_xp(self, server_id: int, discord_id: int, xp: int) -> None:
        self.cur.execute('UPDATE users SET xp = ? WHERE server_id = ? AND discord_id = ?', (xp, server_id, discord_id))
        self.con.commit()


    def get_leaderboard(self, server_id: int) -> list[tuple[str, int]]:
        self.cur.execute('SELECT username, xp FROM users WHERE server_id = ? ORDER BY xp DESC', (server_id,))
        return self.cur.fetchmany(10)


    def get_stats(self, server_id, discord_id: int) -> tuple[str, int, int]:
        self.cur.execute('SELECT username, msg_count, voice_uptime FROM users WHERE server_id = ? AND discord_id = ?', (server_id, discord_id))
        return self.cur.fetchone()
