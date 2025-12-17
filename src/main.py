import os
import time
from dotenv import load_dotenv

from globals import *
import commands
import data
import events

def on_exit():
    server: data.Server
    for server in cached.data.values():
        voice_update: data.VoiceUpdate
        for voice_update in server.voice_updates.values():
            if voice_update.is_connected:
                uptime = time.time() // 60 - voice_update.update_time // 60
                db.add_user_xp(server.id, voice_update.user_id, server.rate_voice * uptime)
                db.add_user_voice_uptime(server.id, voice_update.user_id, uptime)


load_dotenv()
token = os.environ.get('DISCORD_TOKEN')


if __name__ == '__main__':
    bot.run(token)
    on_exit()
