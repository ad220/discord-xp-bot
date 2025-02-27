import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import data

GUILD_ID = 1334451132864659500

load_dotenv()
token = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)
db = data.Database()

@bot.event
async def on_ready():
    db.create_tables()
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_guild_join(guild):
    db.add_server(guild.id, guild.name)
    users = [(member.name, member.id) for member in guild.members]
    db.init_users(guild.id, users)

@bot.event
async def on_guild_remove(guild):
    db.rm_server(int(guild.id))


xpbot = bot.create_group('xpbot', "Manage XP Bot", guild_ids=[GUILD_ID])

@xpbot.command(guild_ids=[GUILD_ID])
async def test(ctx: commands.Context):
    if ctx.author.guild_permissions.administrator:
        await ctx.respond('Test command')
    else:
        await ctx.respond('You do not have permission to use this command')

@xpbot.command(guild_ids=[GUILD_ID])
async def get_leaderboard(ctx: commands.Context):
    users = db.get_leaderboard(ctx.guild.id)
    await ctx.respond(users)


role = xpbot.create_subgroup('role', "Manage automatic roles", guild_ids=[GUILD_ID])

@role.command(guild_ids=[GUILD_ID])
async def add(ctx: commands.Context, role: discord.Role, xp_threshold: int):
    if ctx.author.guild_permissions.administrator:
        db.set_role(ctx.guild.id, role.id, xp_threshold)
        await ctx.respond('Done')
    else:
        await ctx.respond('You do not have permission to use this command')

@role.command(guild_ids=[GUILD_ID])
async def rm(ctx: commands.Context, role: discord.Role):
    if ctx.author.guild_permissions.administrator:
        db.rm_role(role.id)
        await ctx.respond('Done')
    else:
        await ctx.respond('You do not have permission to use this command')

@role.command(guild_ids=[GUILD_ID])
async def show(ctx: commands.Context):
    if ctx.author.guild_permissions.administrator:
        roles = db.get_server_config(ctx.guild.id)['roles']
        await ctx.respond(roles)
    else:
        await ctx.respond('You do not have permission to use this command')


xprate = xpbot.create_subgroup('set_xp_rate', "Manage XP rate", guild_ids=[GUILD_ID])

@xprate.command(guild_ids=[GUILD_ID])
async def voice(ctx: commands.Context, xp_rate: int):
    if ctx.author.guild_permissions.administrator:
        db.set_xp_rate_voice(ctx.guild.id, xp_rate)
        await ctx.respond('Done')
    else:
        await ctx.respond('You do not have permission to use this command')

@xprate.command(guild_ids=[GUILD_ID])
async def text(ctx: commands.Context, xp_rate: int):
    if ctx.author.guild_permissions.administrator:
        db.set_xp_rate_text(ctx.guild.id, xp_rate)
        await ctx.respond('Done')
    else:
        await ctx.respond('You do not have permission to use this command')


bot.run(token)


