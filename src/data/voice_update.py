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
    