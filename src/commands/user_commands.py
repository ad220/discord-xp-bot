from globals import *
from utils.helpers import *


@bot.command(description="Shows the top 10 most active users of the server")
async def leaderboard(ctx: commands.Context):
    users = db.get_users(ctx.guild.id, 10)
    embed = discord.Embed(
        title="Leaderboard",
        color=0x82c778,
    )
    user_column, xp_column = [], []
    for i, user in enumerate(users):
        user_column.append(f"`{i+1}.` <@{user.discord_id}>")
        xp_column.append(f"`{user.xp}`")

    embed.add_field(name="Top 10", value="\n".join(user_column), inline=True)
    embed.add_field(name="XP", value="\n".join(xp_column), inline=True)
    await ctx.respond(embed=embed)

@bot.command(description="Shows your stats on this server")
async def stats(ctx: commands.Context):
    user = db.get_user(ctx.guild.id, ctx.author.id)
    embed = discord.Embed(
        title=f"{user.username}'s stats",
        color=0x82c778,
    )
    embed.add_field(name="XP", value=f"{user.xp} XP", inline=False)
    embed.add_field(name=":coin:", value=f"{user.currency}", inline=False)
    embed.add_field(name="Texts", value=f"{user.msg_count} msg", inline=True)
    embed.add_field(name="Vocal", value=f"{user.voice_uptime//60}h{user.voice_uptime%60:02d}", inline=True)
    await ctx.respond(embed=embed)

@bot.command(description="Shows the roles and the XP required to get them")
async def info(ctx: commands.Context):
    server = cached.get_server(ctx.guild.id)
    embed = discord.Embed(
        title="Roles",
        color=0x82c778,
    )
    add_role_fields(embed, server)
    await ctx.respond(embed=embed)