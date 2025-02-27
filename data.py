import sqlite3

DB_PATH = 'data.db'

class Database:
    def __init__(self):
        self.con = sqlite3.connect(DB_PATH)
        self.cur = self.con.cursor()

    
    def __del__(self):
        self.con.close()


    def create_tables(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS servers (id INTEGER PRIMARY KEY, name TEXT, xprate_msg INTEGER, xprate_voice INTEGER)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, discord_id INTEGER, server_id INTEGER, xp INTEGER, msg_count INTEGER, voice_uptime INTEGER)') 
        self.cur.execute('CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY, xp_threshold INTEGER, server_id INTEGER)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, type TEXT, server_id INTEGER)')
        self.con.commit()


    def add_server(self, server_id, server_name):
        self.cur.execute('INSERT INTO servers VALUES (?, ?, ?, ?)', (server_id, server_name, 0, 0))
        self.con.commit()


    def rm_server(self, server_id):
        self.cur.execute('DELETE FROM servers WHERE id = ?', (server_id,))
        self.cur.execute('DELETE FROM users WHERE server_id = ?', (server_id,))
        self.cur.execute('DELETE FROM roles WHERE server_id = ?', (server_id,))
        self.cur.execute('DELETE FROM channels WHERE server_id = ?', (server_id,))
        self.con.commit()


    def init_users(self, server_id, users):
        self.cur.executemany('INSERT INTO users VALUES (?, ?, ?, ?)', [(username, discord_id, server_id, 0) for (username, discord_id) in users])
        self.con.commit()


    def add_user(self, server_id, username, discord_id):
        self.cur.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)', (username, discord_id, server_id, 0, 0, 0))
        self.con.commit()


    def set_role(self, server_id, role_id, xp_threshold):
        # check if role already exists
        self.cur.execute('SELECT * FROM roles WHERE id = ?', (role_id))
        if self.cur.fetchone():
            # update xp_threshold value
            self.cur.execute('UPDATE roles SET xp_threshold = ? WHERE id = ?', (xp_threshold, role_id))
        else:
            self.cur.execute('INSERT INTO roles (id, xp_threshold, server_id) VALUES (?, ?, ?)', (role_id, xp_threshold, server_id))
        self.con.commit()


    def rm_role(self, role_id):
        self.cur.execute('DELETE FROM roles WHERE id = ?', (role_id))
        self.con.commit()


    def edit_channels(self, server_id, channels):
        self.cur.execute('DELETE FROM channels WHERE server_id = ?', (server_id,))
        self.cur.executemany('INSERT INTO channels VALUES (?, ?, ?)', [(channel_id, channel_type, server_id, ) for (channel_id, channel_type) in channels])
        self.con.commit()


    def get_server_config(self, server_id):
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


    def get_user_xp(self, server_id, discord_id):
        self.cur.execute('SELECT xp FROM users WHERE server_id = ? AND discord_id = ?', (server_id, discord_id))
        return self.cur.fetchone()[0]


    def set_user_xp(self, server_id, discord_id, xp):
        self.cur.execute('UPDATE users SET xp = ? WHERE server_id = ? AND discord_id = ?', (xp, server_id, discord_id))
        self.con.commit()


    def get_leaderboard(self, server_id):
        self.cur.execute('SELECT username, xp FROM users WHERE server_id = ? ORDER BY xp DESC', (server_id,))
        return self.cur.fetchall()


    def get_stats(self, server_id, discord_id):
        self.cur.execute('SELECT username, msg_count, voice_uptime FROM users WHERE server_id = ? AND discord_id = ?', (server_id, discord_id))
        return self.cur.fetchone()
