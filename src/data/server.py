from dataclasses import dataclass
import discord

from .role import Role
from .voice_update import VoiceUpdate

@dataclass
class Server():
    id:             int            
    name:           str    
    rate_txt:       int
    rate_voice:     int
    mod_role:       int
    msg_cooldown:   int
    msg_rankthr:    int
    msg_xpfactor:   float
    msg_xpmin:      int
    roles:          list[Role]
    channels:       dict
    voice_updates:  dict[int:VoiceUpdate]
    
    def __str__(self):
        nl = '\n'
        return f"ServerConfig(\n   {f',{nl}   '.join([f'{k}: {v}' for k, v in self.__dict__.items()])}\n)"
    
    def get_voice_update(self, user_id: int) -> VoiceUpdate:
        return self.voice_updates.get(user_id, None)
    
    def add_voice_update(self, member: discord.Member, voice_state: discord.VoiceState):
        update = VoiceUpdate(member, voice_state)
        self.voice_updates[member.id] = update
