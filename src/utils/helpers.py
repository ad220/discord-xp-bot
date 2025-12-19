import time
import datetime
import discord
from discord.ext import commands

import data
from globals import *

def get_user_rank(member: discord.Member, server: data.Server) -> data.Role|None:
    member_roles = [role.id for role in member.roles]
    for role in server.roles:
        if role.id in member_roles:
            return role
    return None

async def update_role(member: discord.Member, server: data.Server, xp: int):
    member_roles = [role.id for role in member.roles]    
    n_role = 0
    while n_role < len(server.roles) and server.roles[n_role].xp_threshold <= xp:
        n_role += 1

    if n_role>0 and server.roles[n_role-1].id not in member_roles:
        await member.remove_roles(*[discord.Object(role.id) for role in server.roles])
        await member.add_roles(discord.Object(server.roles[n_role-1].id))

async def is_mod(ctx: commands.Context):
    mod_role = cached.get_server(ctx.guild.id).mod_role
    if mod_role in [role.id for role in ctx.author.roles]:
        return True
    await ctx.respond(f"You must be <{mod_role}> to use this command")
    return False

def add_channel_fields(embed: discord.Embed, server: data.Server):
    text_channels = [f"<#{channel_id}>" for channel_id in server.channels['text']]
    voice_channels = [f"<#{channel_id}>" for channel_id in server.channels['voice']]
    embed.add_field(name="Text channels", value="\n".join(text_channels), inline=True)
    embed.add_field(name="Voice channels", value="\n".join(voice_channels), inline=True)

def add_role_fields(embed: discord.Embed, server: data.Server):
    role_list = server.roles
    role_column, xp_column, cur_column = [], [], []
    for n, role in enumerate(role_list):
        role_column.append(f"`{n}.` <@&{role.id}>")
        xp_column.append(f"`{role.xp_threshold}`")
        cur_column.append(f"`{role.cur_reward}`")

    embed.add_field(name="Role", value="\n".join(role_column), inline=True)
    embed.add_field(name="XP", value="\n".join(xp_column), inline=True)
    embed.add_field(name=":coin:", value="\n".join(cur_column), inline=True)

def add_xprate_fields(embed: discord.Embed, server: data.Server):
    embed.add_field(name="Text", value=f"`{server.rate_txt}`/msg", inline=True)
    embed.add_field(name="Voice", value=f"`{server.rate_voice}`/min", inline=True)

def is_channel_visible(ctx: commands.context, channel_id: int):
    channel = bot.get_channel(channel_id)
    if channel:
        perms = bot.get_channel(channel.id).permissions_for(ctx.guild.me)
        return perms.read_messages or perms.view_channel
    return False

def check_currency(user: data.User, member: discord.Member, cfg: data.Server):
    date = datetime.date.fromtimestamp(time.time()).toordinal()
    if (date - user.lastcur_date > 0):
        rank = get_user_rank(member, cfg)
        if rank and not member.status in [discord.Status.offline, discord.Status.invisible, discord.Status.idle]:
            user.lastcur_date = date
            user.currency += rank.cur_reward