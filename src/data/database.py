import sqlite3
from discord.enums import ChannelType
import datetime
import time

from .user import User
from .server import Server
from .role import Role
from .history import History

DB_PATH = 'data/data.db'

class Database:
    def __init__(self):
        self.con = sqlite3.connect(DB_PATH)
        self.cur = self.con.cursor()

    
    def __del__(self):
        self.con.close()


    def init(self) -> None: 
        self.cur.execute('CREATE TABLE IF NOT EXISTS servers (id INTEGER PRIMARY KEY, name TEXT, xprate_msg INTEGER DEFAULT 1, xprate_voice INTEGER DEFAULT 1, mod_role INTEGER DEFAULT 0, msg_cooldown INTEGER DEFAULT 0, msg_rankthreshold INTEGER DEFAULT -1, msg_xpfactor REAL DEFAULT 1, msg_xpmin INTEGER DEFAULT 1)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, discord_id INTEGER, server_id INTEGER, xp INTEGER DEFAULT 0, msg_count INTEGER DEFAULT 0, voice_uptime INTEGER DEFAULT 0, lastmsg_time INTEGER DEFAULT 0, lastmsg_xp INTEGER DEFAULT 0, currency INTEGER DEFAULT 0, lastcur_date INTEGER DEFAULT 0)') 
        self.cur.execute('CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY, xp_threshold INTEGER, server_id INTEGER, cur_reward INTEGER DEFAULT 0)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, type INTEGER, server_id INTEGER)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, user_id INTEGER, server_id INTEGER, date INTEGER, xp INTEGER, msg INTEGER, voice_uptime INTEGER, currency INTEGER)')
        self.con.commit()
        
        self.cur.execute('PRAGMA table_info(servers)')
        nb_columns = len(self.cur.fetchall())
        if nb_columns == 5:
            self.cur.execute('ALTER TABLE servers ADD COLUMN msg_cooldown INTEGER DEFAULT 0')
            self.cur.execute('ALTER TABLE servers ADD COLUMN msg_rankthreshold INTEGER DEFAULT -1')
            self.cur.execute('ALTER TABLE servers ADD COLUMN msg_xpfactor REAL DEFAULT 1')
            self.cur.execute('ALTER TABLE servers ADD COLUMN msg_xpmin INTEGER DEFAULT 1')
            self.con.commit()
        elif nb_columns != 9:
            self.con.close()
            raise Exception('Database schema is unknown')

        self.cur.execute('PRAGMA table_info(users)')
        nb_columns = len(self.cur.fetchall())
        if nb_columns == 7:
            self.cur.execute('ALTER TABLE users ADD COLUMN lastmsg_time INTEGER DEFAULT 0')
            self.cur.execute('ALTER TABLE users ADD COLUMN lastmsg_xp INTEGER DEFAULT 0')
            self.con.commit()
        elif nb_columns == 9:
            self.cur.execute('ALTER TABLE users ADD COLUMN currency INTEGER DEFAULT 0')
            self.cur.execute('ALTER TABLE users ADD COLUMN lastcur_date INTEGER DEFAULT 0')
        elif nb_columns != 11:
            self.con.close()
            raise Exception('Database schema is unknown')
        
        self.cur.execute('PRAGMA table_info(roles)')
        nb_columns = len(self.cur.fetchall())
        if nb_columns == 3:
            self.cur.execute('ALTER TABLE roles ADD COLUMN cur_reward INTEGER DEFAULT 0')
        elif nb_columns != 4:
            self.con.close()
            raise Exception('Database schema is unknown')


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


    def set_role(self, role: Role) -> None:
        # check if role already exists
        self.cur.execute('SELECT * FROM roles WHERE id = ?', (role.id,))
        if self.cur.fetchone():
            # update xp_threshold value
            self.cur.execute('UPDATE roles SET (xp_threshold, cur_reward) = (?, ?) WHERE id = ?', (role.xp_threshold, role.cur_reward, role.id))
        else:
            self.cur.execute('INSERT INTO roles (id, xp_threshold, server_id, cur_reward) VALUES (?, ?, ?, ?)', role.to_db())
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


    def get_server(self, server_id: int) -> Server:
        self.cur.execute('SELECT * FROM servers WHERE id = ?', (server_id,))
        params = self.cur.fetchone()

        self.cur.execute('SELECT * FROM roles WHERE server_id = ? ORDER BY xp_threshold ASC', (server_id,))
        roles = [Role(*r) for r in self.cur.fetchall()]

        channels = {}
        self.cur.execute('SELECT id FROM channels WHERE server_id = ? AND type = ?', (server_id, ChannelType.text.value))
        channels['text'] = [channel[0] for channel in self.cur.fetchall()]

        self.cur.execute('SELECT id FROM channels WHERE server_id = ? AND type = ?', (server_id, ChannelType.voice.value))
        channels['voice'] = [channel[0] for channel in self.cur.fetchall()]

        return Server(*params, roles, channels, {})
    

    def set_xp_rate_text(self, server_id: int, xp_rate: int, msg_cooldown: int, msg_rankthr: int, msg_xpfactor: float, msg_xpmin: int) -> int:
        self.cur.execute('UPDATE servers SET (xprate_msg, msg_cooldown, msg_rankthreshold, msg_xpfactor, msg_xpmin) = (?, ?, ?, ?, ?) WHERE id = ?', (xp_rate, msg_cooldown, msg_rankthr, msg_xpfactor, msg_xpmin, server_id))
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


    def get_user_currency(self, server_id: int, user_id: int) -> int:
        self.cur.execute('SELECT currency FROM users WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        return self.cur.fetchone()[0]
    
    def set_user_currency(self, server_id: int, user_id: int, currency: int) -> None:
        self.cur.execute('UPDATE users SET currency = ? WHERE server_id = ? AND discord_id = ?', (currency, server_id, user_id))
        self.con.commit()
    
    def add_user_currency(self, server_id: int, user_id: int, currency: int) -> None:
        self.cur.execute('UPDATE users SET currency = currency + ? WHERE server_id = ? AND discord_id = ?', (currency, server_id, user_id))
        self.con.commit()


    def get_user(self, server_id, user_id: int) -> User:
        self.cur.execute('SELECT * FROM users WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        return User(*self.cur.fetchone())

    def get_users(self, server_id: int, n_users: int = None) -> list[User]:
        self.cur.execute('SELECT * FROM users WHERE server_id = ? ORDER BY xp DESC', (server_id,))
        result = self.cur.fetchmany(n_users) if n_users else self.cur.fetchall()

        users = []
        for params in result:
            users.append(User(*params))
        return users
    
    def update_user(self, server_id: int, user_id: int, xp: int|None = None, msg_count: int|None = None, voice_uptime: int|None = None, lastmsg_time: int|None = None, lastmsg_xp: int|None = None, currency: int|None = None, lastcur_date: int|None = None) -> None:
        updated = False
        if xp is not None:
            self.cur.execute('UPDATE users SET xp = ? WHERE server_id = ? AND discord_id = ?', (xp, server_id, user_id))
            updated = True
        if msg_count is not None:
            self.cur.execute('UPDATE users SET msg_count = ? WHERE server_id = ? AND discord_id = ?', (msg_count, server_id, user_id))
            updated = True
        if voice_uptime is not None:
            self.cur.execute('UPDATE users SET voice_uptime = ? WHERE server_id = ? AND discord_id = ?', (voice_uptime, server_id, user_id))
            updated = True
        if lastmsg_time is not None:
            self.cur.execute('UPDATE users SET lastmsg_time = ? WHERE server_id = ? AND discord_id = ?', (lastmsg_time, server_id, user_id))
            updated = True
        if lastmsg_xp is not None:
            self.cur.execute('UPDATE users SET lastmsg_xp = ? WHERE server_id = ? AND discord_id = ?', (lastmsg_xp, server_id, user_id))
            updated = True
        if currency is not None:
            self.cur.execute('UPDATE users SET currency = ? WHERE server_id = ? AND discord_id = ?', (currency, server_id, user_id))
            updated = True
        if lastcur_date is not None:
            self.cur.execute('UPDATE users SET lastcur_date = ? WHERE server_id = ? AND discord_id = ?', (lastcur_date, server_id, user_id))
            updated = True
        if updated:
            self.con.commit()


    def get_history(self, server_id: int, user_id: int, record_count: int|None = None) -> int:
        self.cur.execute('SELECT * FROM history WHERE server_id = ? AND discord_id = ?', (server_id, user_id))
        result = self.cur.fetchmany(record_count) if record_count else self.cur.fetchall()
        return [History(*params) for params in result]
    
    def add_history_records(self, server_id: int, users: list[User]) -> None:
        date = datetime.date.fromtimestamp(time.time()).toordinal()
        for u in users:
            self.cur.execute('INSERT INTO history (user_id, server_id, date, xp, msg, voice_uptime, currency) VALUES (?, ?, ?, ?, ?, ?, ?)', (u.discord_id, server_id, date, u.xp, u.msg_count, u.voice_uptime, u.currency))
        self.con.commit()
