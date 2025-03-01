import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import data
import cache
from cache import ServerConfig

GUILD_ID = 1334451132864659500

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
    max_thr = -1
    new_role = None
    member_roles = [role.id for role in member.roles]
    for role_id, role_thr in server_config.roles:
        if role_id in member_roles:
            current_role = role_id
        elif role_thr > max_thr and xp >= role_thr:
            max_thr = role_thr
            new_role = role_id
    if new_role:
        await member.add_roles(discord.Object(new_role))
        await member.remove_roles(discord.Object(current_role))


async def is_mod(ctx: commands.Context):
    mod_role = cached.get_server(ctx.guild.id).config.mod_role
    if mod_role in [role.id for role in ctx.author.roles]:
        return True
    await ctx.respond(f"You must be <@&{mod_role}> to use this command")
    return False


# ================================
# Events
# ================================

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.invisible)
    db.create_tables()
    servers = db.get_servers()
    for server in servers:
        cached.add_server(db.get_server_config(server))
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

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    server_config = cached.get_server(message.guild.id).config
    if message.channel.id in server_config.channels['text']:
        xp = db.add_user_xp(message.guild.id, message.author.id, server_config.rate_txt)
        db.add_user_msg_count(message.guild.id, message.author.id)
        await update_role(message.author, server_config, xp)


@bot.event
async def on_voice_state_update(member: discord.Member,
                                before: discord.VoiceState,
                                after: discord.VoiceState):
    server = cached.get_server(member.guild.id)
    # If user disconnected from voice channel and a past update exist in cached data,
    # calculate the time spent in voice channel and update the user xp
    if before.channel is not None and after.channel is None:
        last_voice_update = server.get_voice_update(member.id)
        if last_voice_update:
            uptime = last_voice_update.uptime(cache.VoiceUpdate(member, after))
            xp = db.add_user_xp(member.guild.id, member.id, server.config.rate_voice * uptime)
            db.add_user_voice_uptime(member.guild.id, member.id, uptime)
            await update_role(member, server.config, xp)
    # If user connected to voice channel, create a new voice update
    elif before.channel is None and after.channel is not None:
        server.add_voice_update(member, after)


# ================================
# Commands
# ================================

xpbot = bot.create_group('xpbot', "Manage XP Bot", guild_ids=[GUILD_ID])

# User commands
@xpbot.command(guild_ids=[GUILD_ID])
async def leaderboard(ctx: commands.Context):
    users = db.get_leaderboard(ctx.guild.id)
    embed = discord.Embed(
        title="Leaderboard",
        color=0x82c778,
    )
    user_column, xp_column = [], []
    for i, user in enumerate(users):
        username, xp = user
        user_column.append(f"`{i+1}.` {username}")
        xp_column.append(f"`{xp}`")

    embed.add_field(name="Top 10", value="\n".join(user_column), inline=True)
    embed.add_field(name="XP", value="\n".join(xp_column), inline=True)
    await ctx.respond(embed=embed)

@xpbot.command(guild_ids=[GUILD_ID])
async def stats(ctx: commands.Context):
    stats = db.get_stats(ctx.guild.id, ctx.author.id)
    username, xp, msg_count, voice_uptime = stats
    embed = discord.Embed(
        title=f"{username}'s stats",
        color=0x82c778,
    )
    embed.add_field(name="XP", value=f"{xp} XP")
    embed.add_field(name="Texts", value=f"{msg_count} msg")
    embed.add_field(name="Vocal", value=f"{voice_uptime//60}h{voice_uptime%60:02d}")
    await ctx.respond(embed=embed)


# Mod commands
@xpbot.command(guild_ids=[GUILD_ID])
async def set_xp(ctx: commands.Context, member: discord.Member, xp: int):
    if await is_mod(ctx):
        db.set_user_xp(ctx.guild.id, member.id, xp)
        await update_role(member, db.get_server_config(ctx.guild.id), xp)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@xpbot.command(guild_ids=[GUILD_ID])
async def set_channels(ctx: commands.Context):
    if await is_mod(ctx):
        await ctx.respond('Select the channels you want to track', view=ChannelView())

class ChannelView(discord.ui.View):
    @discord.ui.select(
        select_type=discord.ComponentType.channel_select,
        max_values=25,
        min_values=1,
        channel_types=[discord.ChannelType.text, discord.ChannelType.voice]
    )
    async def select_callback(self, select, interaction):
        db.edit_channels(interaction.guild.id, [(channel.id, channel.type.value) for channel in select.values])
        cached.update_server_config(db.get_server_config(interaction.guild.id))
        await interaction.response.send_message('Done', ephemeral=True)

# Admin commands
@xpbot.command(guild_ids=[GUILD_ID])
async def set_mod_role(ctx: commands.Context, role: discord.Role):
    if ctx.author.guild_permissions.administrator:
        db.set_mod_role(ctx.guild.id, role.id)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')
    else:
        await ctx.respond('You must be an administrator to use this command')


role = xpbot.create_subgroup('role', "Manage automatic roles", guild_ids=[GUILD_ID])

@role.command(guild_ids=[GUILD_ID])
async def add(ctx: commands.Context, role: discord.Role, xp_threshold: int):
    if await is_mod(ctx):
        db.set_role(ctx.guild.id, role.id, xp_threshold)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@role.command(guild_ids=[GUILD_ID])
async def rm(ctx: commands.Context, role: discord.Role):
    if await is_mod(ctx):
        db.rm_role(role.id)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@role.command(guild_ids=[GUILD_ID])
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        roles = db.get_server_config(ctx.guild.id)['roles']
        await ctx.respond(roles)


xprate = xpbot.create_subgroup('set_xp_rate', "Manage XP rate", guild_ids=[GUILD_ID])

@xprate.command(guild_ids=[GUILD_ID])
async def voice(ctx: commands.Context, xp_rate: int):
    if await is_mod(ctx):
        db.set_xp_rate_voice(ctx.guild.id, xp_rate)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')

@xprate.command(guild_ids=[GUILD_ID])
async def text(ctx: commands.Context, xp_rate: int):
    if await is_mod(ctx):
        db.set_xp_rate_text(ctx.guild.id, xp_rate)
        cached.update_server_config(db.get_server_config(ctx.guild.id))
        await ctx.respond('Done')


bot.run(token)


