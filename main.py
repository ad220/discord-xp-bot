import os
import time
import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv

import data
import cache
from cache import ServerConfig

load_dotenv()
token = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)
db = data.Database()
cached = cache.CachedData()


# ================================
# Functions
# ================================

async def update_role(member: discord.Member, server_config: ServerConfig, xp: int):
    member_roles = [role.id for role in member.roles]    
    n_role = 0
    while n_role < len(server_config.roles) and server_config.roles[n_role][1] <= xp:
        n_role += 1

    if n_role>0 and server_config.roles[n_role-1][0] not in member_roles:
        await member.remove_roles(*[discord.Object(role_id) for role_id, _ in server_config.roles])
        await member.add_roles(discord.Object(server_config.roles[n_role-1][0]))

async def is_mod(ctx: commands.Context):
    mod_role = cached.get_server(ctx.guild.id).config.mod_role
    if mod_role in [role.id for role in ctx.author.roles]:
        return True
    await ctx.respond(f"You must be <{mod_role}> to use this command")
    return False

def add_channel_fields(embed: discord.Embed, server_config: ServerConfig):
    text_channels = [f"<#{channel_id}>" for channel_id in server_config.channels['text']]
    voice_channels = [f"<#{channel_id}>" for channel_id in server_config.channels['voice']]
    embed.add_field(name="Text channels", value="\n".join(text_channels), inline=True)
    embed.add_field(name="Voice channels", value="\n".join(voice_channels), inline=True)

def add_role_fields(embed: discord.Embed, server_config: ServerConfig):
    role_list = server_config.roles
    role_column = []
    xp_column = []
    for n, (role_id, xp) in enumerate(role_list):
        role_column.append(f"`{n}.` <@&{role_id}>")
        xp_column.append(f"`{xp}`")

    embed.add_field(name="Role", value="\n".join(role_column), inline=True)
    embed.add_field(name="XP required", value="\n".join(xp_column), inline=True)

def add_xprate_fields(embed: discord.Embed, server_config: ServerConfig):
    embed.add_field(name="Text", value=f"`{server_config.rate_txt}`/msg", inline=True)
    embed.add_field(name="Voice", value=f"`{server_config.rate_voice}`/min", inline=True)

def is_channel_visible(ctx: commands.context, channel_id: int):
    channel = bot.get_channel(channel_id)
    if channel:
        perms = bot.get_channel(channel.id).permissions_for(ctx.guild.me)
        return perms.read_messages or perms.view_channel
    return False

def on_exit():
    server: cache.CachedServer
    for server in cached.data.values():
        voice_update: cache.VoiceUpdate
        for voice_update in server.voice_updates.values():
            if voice_update.is_connected:
                uptime = time.time() // 60 - voice_update.update_time // 60
                db.add_user_xp(server.id, voice_update.user_id, server.config.rate_voice * uptime)
                db.add_user_voice_uptime(server.id, voice_update.user_id, uptime)


# ================================
# Events
# ================================

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.invisible)
    db.init()
    servers = db.get_servers()
    for server in servers:
        config = db.get_server_config(server)
        cached.add_server(config)

        guild = bot.get_guild(server)
        users = db.get_users(server)
        user_ids = [discord_id for _, discord_id, _, _, _, _, _ in users]
        for member in guild.members:
            if not member.id in user_ids:
                db.add_user(server, member.id, member.name)
        for channel in config.channels['voice']:
            voice_states: dict[int:discord.VoiceState] = bot.get_channel(channel).voice_states
            for user_id in voice_states:
                member = bot.get_guild(server).get_member(user_id)
                cached.get_server(server).add_voice_update(member, voice_states[user_id])
        
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_guild_join(guild: discord.Guild):
    db.add_server(guild.id, guild.name)
    users = [(member.name, member.id) for member in guild.members]
    db.init_users(guild.id, users)
    cached.add_server(db.get_server_config(guild.id))

@bot.event
async def on_guild_remove(guild: discord.Guild):
    db.rm_server(guild.id)
    cached.rm_server(guild.id)

@bot.event
async def on_member_join(member):
    db.add_user(member.guild.id, member.id, member.name)
    server_config = cached.get_server(member.guild.id).config
    await update_role(member, server_config, 0)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    server_config = cached.get_server(message.guild.id).config
    if message.channel.id in server_config.channels['text']:
        _, xp, msg_count, _, lastmsg_time, lastmsg_xp = db.get_user(message.guild.id, message.author.id)
        msg_count += 1
        newmsg_time = time.time()
        if newmsg_time - lastmsg_time >= server_config.msg_cooldown:
            is_new_user = server_config.msg_rankthr == -1 or xp < server_config.msg_rankthr
            new_date = datetime.datetime.fromtimestamp(newmsg_time)
            last_date = datetime.datetime.fromtimestamp(lastmsg_time)
            if is_new_user or new_date.date() != last_date.date():
                xp += server_config.rate_txt
                lastmsg_xp = server_config.rate_txt
            else:
                new_xp = max(int(lastmsg_xp * server_config.msg_xpfactor), server_config.msg_xpmin)
                xp += new_xp
                lastmsg_xp = new_xp
            db.update_user(message.guild.id, message.author.id, msg_count=msg_count, xp=xp, lastmsg_time=newmsg_time, lastmsg_xp=lastmsg_xp)
            await update_role(message.author, server_config, xp)
        else:
            db.update_user(message.guild.id, message.author.id, msg_count=msg_count)

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
            uptime = last_voice_update.uptime(cache.VoiceUpdate(member, after))
            xp = db.add_user_xp(member.guild.id, member.id, server.config.rate_voice * uptime)
            db.add_user_voice_uptime(member.guild.id, member.id, uptime)
            await update_role(member, server.config, xp)
            server.add_voice_update(member, after)
    # If user connected to voice channel, create a new voice update
    elif before.channel is None and after.channel is not None:
        server.add_voice_update(member, after)


# ================================
# Commands
# ================================

# User commands
@bot.command(description="Shows the top 10 most active users of the server")
async def leaderboard(ctx: commands.Context):
    users = db.get_users(ctx.guild.id, 10)
    embed = discord.Embed(
        title="Leaderboard",
        color=0x82c778,
    )
    user_column, xp_column = [], []
    for i, user in enumerate(users):
        _, discord_id, xp, _, _, _, _ = user
        user_column.append(f"`{i+1}.` <@{discord_id}>")
        xp_column.append(f"`{xp}`")

    embed.add_field(name="Top 10", value="\n".join(user_column), inline=True)
    embed.add_field(name="XP", value="\n".join(xp_column), inline=True)
    await ctx.respond(embed=embed)

@bot.command(description="Shows your stats on this server")
async def stats(ctx: commands.Context):
    stats = db.get_user(ctx.guild.id, ctx.author.id)
    username, xp, msg_count, voice_uptime, _, _ = stats
    embed = discord.Embed(
        title=f"{username}'s stats",
        color=0x82c778,
    )
    embed.add_field(name="XP", value=f"{xp} XP")
    embed.add_field(name="Texts", value=f"{msg_count} msg")
    embed.add_field(name="Vocal", value=f"{voice_uptime//60}h{voice_uptime%60:02d}")
    await ctx.respond(embed=embed)

@bot.command(description="Shows the roles and the XP required to get them")
async def info(ctx: commands.Context):
    server_config = cached.get_server(ctx.guild.id).config
    embed = discord.Embed(
        title="Roles",
        color=0x82c778,
    )
    add_role_fields(embed, server_config)
    await ctx.respond(embed=embed)


# Mod commands

@bot.command()
async def user_xp(ctx: commands.Context, member: discord.Member, xp: int):
    if await is_mod(ctx):
        db.set_user_xp(ctx.guild.id, member.id, xp)
        await update_role(member, db.get_server_config(ctx.guild.id), xp)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')


@bot.command()
async def refresh_roles(ctx: commands.Context):
    if await is_mod(ctx):
        await ctx.send('Refreshing roles...')
        server_config = cached.get_server(ctx.guild.id).config
        users = db.get_users(ctx.guild.id)
        for _, discord_id, xp, _, _, _, _ in users:
            member = ctx.guild.get_member(discord_id)
            await update_role(member, server_config, xp)
        await ctx.respond('Done')


config = bot.create_group('config', "Manage bot configuration for this server")

@config.command(description="Show the full bot configuration for this server")
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        server_config = cached.get_server(ctx.guild.id).config
        embed = discord.Embed(
            title="XP Bot configuration",
            color=0x82c778,
        )
        embed.add_field(name="Mod role", value=f"<@&{server_config.mod_role}>", inline=False)
        embed.add_field(name=" ", value="**=== Automatic roles ===**", inline=False)
        add_role_fields(embed, server_config)
        embed.add_field(name=" ", value="**=== Tracked channels ===**", inline=False)
        add_channel_fields(embed, server_config)
        embed.add_field(name=" ", value="**=== XP rates ===**", inline=False)
        add_xprate_fields(embed, server_config)
        await ctx.respond(embed=embed)


channel = config.create_subgroup('channel', "Manage channels")

@channel.command(description="Add a channel to the list of channels to track")
async def add(ctx: commands.Context, channel: discord.TextChannel | discord.VoiceChannel):
    if await is_mod(ctx):
        db.add_channel(ctx.guild.id, channel.id, channel.type.value)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        if not is_channel_visible(ctx, channel.id):
            await ctx.respond(f"Warning: I cannot see <#{channel.id}>, please check my permissions")
        await ctx.respond('Done')

@channel.command(description="Remove a channel from the list of channels to track")
async def rm(ctx: commands.Context, channel: discord.TextChannel | discord.VoiceChannel):
    if await is_mod(ctx):
        db.rm_channel(channel.id)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@channel.command(description="Show the list of channels to track")
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        server_config = cached.get_server(ctx.guild.id).config
        embed = discord.Embed(
            title="Channels",
            color=0x82c778,
        )
        add_channel_fields(embed, server_config)
        await ctx.respond(embed=embed)
        
        unavailable_channels = []
        for channel_id in server_config.channels['text'] + server_config.channels['voice']:
            if not is_channel_visible(ctx, channel_id):
                unavailable_channels.append(f"<#{channel_id}>")
        if unavailable_channels:
            await ctx.send(f"Warning: I cannot see the following channels {', '.join(unavailable_channels)}, please check my permissions")


role = config.create_subgroup('role', "Manage automatic roles")

@role.command(description="Add a role to the list of automatic roles")
async def add(ctx: commands.Context, role: discord.Role, xp_threshold: int):
    if await is_mod(ctx):
        db.set_role(ctx.guild.id, role.id, xp_threshold)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@role.command(description="Remove a role from the list of automatic roles")
async def rm(ctx: commands.Context, role: discord.Role):
    if await is_mod(ctx):
        db.rm_role(role.id)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@role.command(description="Show the list of automatic roles")
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        await info(ctx)


rate = config.create_subgroup('rate', "Manage XP rate")

@rate.command(description="Set the XP rate for text channel. Check documentation for more info")
async def text(ctx: commands.Context, base_xp_per_msg: int, cooldown_in_sec: int = 0, xp_factor: float = 1, min_xp: int = 1, rank_xp_threshold: int = -1):
    if await is_mod(ctx):
        db.set_xp_rate_text(ctx.guild.id, base_xp_per_msg, cooldown_in_sec, rank_xp_threshold, xp_factor, min_xp)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@rate.command(description="Set the XP rate for voice channels")
async def voice(ctx: commands.Context, xp_per_minute: int):
    if await is_mod(ctx):
        db.set_xp_rate_voice(ctx.guild.id, xp_per_minute)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@rate.command(description="Show the XP rate for text and voice channels")
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        server_config = cached.get_server(ctx.guild.id).config
        embed = discord.Embed(
            title="XP rate",
            color=0x82c778,
        )
        add_xprate_fields(embed, server_config)
        await ctx.respond(embed=embed)


# Admin commands
@config.command()
async def mod_role(ctx: commands.Context, role: discord.Role):
    if ctx.author.guild_permissions.administrator:
        db.set_mod_role(ctx.guild.id, role.id)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')
    else:
        await ctx.respond('You must be an administrator to use this command')


if __name__ == '__main__':
    bot.run(token)
    on_exit()
