import time
import discord
from typing import Self


class VoiceUpdate():
    def __init__(self, member: discord.Member, voice_state: discord.VoiceState):
        self.update_time = time.time()
        self.is_connected = voice_state.channel is not None
        self.user_id = member.id
    
    def uptime(self, new_update: Self) -> int:
        return new_update.update_time // 60 - self.update_time // 60


class ServerConfig():
    def __init__(self,
                 server_id: int,
                 name: str,
                 rate_txt: int,
                 rate_voice: int,
                 mod_role: int,
                 roles: dict[int:int],
                 channels: dict):
        self.id: int = server_id
        self.name: str = name
        self.rate_txt: int = rate_txt
        self.rate_voice: int = rate_voice
        self.mod_role: int = mod_role
        self.roles: list[tuple[int, int]] = roles
        self.channels: dict = channels    


class CachedServer():
    def __init__(self, config: ServerConfig):
        self.id: int = config.id
        self.config: ServerConfig = config
        self.voice_updates: dict[int:VoiceUpdate] = {}

    def update_config(self, config: ServerConfig):
        self.config = config

    def get_voice_update(self, user_id: int) -> VoiceUpdate:
        return self.voice_updates.get(user_id, None)
    
    def add_voice_update(self, member: discord.Member, voice_state: discord.VoiceState):
        update = VoiceUpdate(member, voice_state)
        self.voice_updates[member.id] = update




class CachedData():
    def __init__(self):
        self.data: dict[int:CachedServer] = {}
    
    def get_server(self, server_id: int) -> CachedServer:
        return self.data.get(server_id, None)
    
    def add_server(self, config: ServerConfig):
        self.data[config.id] = CachedServer(config)

    def rm_server(self, server_id: int):
        del self.data[server_id]
    
    def update_server_config(self, config: ServerConfig):
        self.data[config.id].update_config(config)
    
