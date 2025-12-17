from globals import *
from utils.helpers import *

@bot.command()
async def user_xp(ctx: commands.Context, member: discord.Member, xp: int):
    if await is_mod(ctx):
        db.set_user_xp(ctx.guild.id, member.id, xp)
        await update_role(member, db.get_server(ctx.guild.id), xp)
        cached.update_server_config(db.get_server(ctx.guild.id))
        await ctx.respond('Done')


@bot.command()
async def refresh_roles(ctx: commands.Context):
    if await is_mod(ctx):
        await ctx.send('Refreshing roles...')
        server = cached.get_server(ctx.guild.id)
        users = db.get_users(ctx.guild.id)
        for u in users:
            member = ctx.guild.get_member(u.discord_id)
            await update_role(member, server, u.xp)
        await ctx.respond('Done')
