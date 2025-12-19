import time
import datetime

from globals import *
from utils.helpers import *
from utils.tasks import daily_tasks

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.invisible)
    db.init()
    servers = db.get_servers()
    for server in servers:
        config = db.get_server(server)
        cached.add_server(config)

        guild = bot.get_guild(server)
        users = db.get_users(server)
        user_ids = [u.discord_id for u in users]
        for member in guild.members:
            if not member.id in user_ids:
                db.add_user(server, member.id, member.name)
        for channel in config.channels['voice']:
            voice_states: dict[int:discord.VoiceState] = bot.get_channel(channel).voice_states
            for user_id in voice_states:
                member = bot.get_guild(server).get_member(user_id)
                cached.get_server(server).add_voice_update(member, voice_states[user_id])
    
    print("bot ready")
    daily_tasks.start()
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_guild_join(guild: discord.Guild):
    db.add_server(guild.id, guild.name)
    users = [(member.name, member.id) for member in guild.members]
    db.init_users(guild.id, users)
    cached.add_server(db.get_server(guild.id))

@bot.event
async def on_guild_remove(guild: discord.Guild):
    db.rm_server(guild.id)
    cached.rm_server(guild.id)

@bot.event
async def on_member_join(member):
    db.add_user(member.guild.id, member.id, member.name)
    server = cached.get_server(member.guild.id)
    await update_role(member, server, 0)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    server = cached.get_server(message.guild.id)
    if message.channel.id in server.channels['text']:
        user = db.get_user(message.guild.id, message.author.id)
        user.msg_count += 1
        
        check_currency(user, message.author, server)

        newmsg_time = time.time()
        if newmsg_time - user.lastmsg_time >= server.msg_cooldown:
            is_new_user = server.msg_rankthr == -1 or user.xp < server.msg_rankthr
            new_date = datetime.datetime.fromtimestamp(newmsg_time)
            last_date = datetime.datetime.fromtimestamp(user.lastmsg_time)
            if is_new_user or new_date.date() != last_date.date():
                user.xp += server.rate_txt
                user.lastmsg_xp = server.rate_txt
            else:
                new_xp = max(int(user.lastmsg_xp * server.msg_xpfactor), server.msg_xpmin)
                user.xp += new_xp
                user.lastmsg_xp = new_xp
            db.update_user(
                message.guild.id,
                message.author.id,
                msg_count       = user.msg_count,
                xp              = user.xp,
                lastmsg_time    = newmsg_time,
                lastmsg_xp      = user.lastmsg_xp,
                currency        = user.currency,
                lastcur_date    = user.lastcur_date
            )
            await update_role(message.author, server, user.xp)
        else:
            db.update_user(
                message.guild.id,
                message.author.id,
                msg_count       = user.msg_count,
                currency        = user.currency,
                lastcur_date    = user.lastcur_date
            )
        

@bot.event
async def on_voice_state_update(member: discord.Member,
                                before: discord.VoiceState,
                                after: discord.VoiceState):
    server = cached.get_server(member.guild.id)
    # If user disconnected from voice channel and a past update exist in cached data,
    # calculate the time spent in voice channel and update the user xp
    if before.channel is not None and after.channel is None:
        last_voice_update = server.get_voice_update(member.id)
        if last_voice_update and last_voice_update.is_connected:
            user = db.get_user(server.id, member.id)

            check_currency(user, member, server)

            uptime = last_voice_update.uptime(data.VoiceUpdate(member, after))
            user.voice_uptime += uptime
            user.xp += server.rate_voice * uptime

            await update_role(member, server, user.xp)

            server.add_voice_update(member, after)
            db.update_user(
                server.id,
                member.id,
                xp=user.xp,
                voice_uptime=user.voice_uptime,
                currency=user.currency
            )
    
    # If user connected to voice channel, create a new voice update
    elif before.channel is None and after.channel is not None:
        server.add_voice_update(member, after)
