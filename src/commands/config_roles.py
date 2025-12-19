from .config import *
from .user_commands import info

role = config.create_subgroup('role', "Manage automatic roles")

@role.command(description="Add a role to the list of automatic roles")
async def add(ctx: commands.Context, role: discord.Role, xp_threshold: int, currency_reward: int):
    if await is_mod(ctx):
        role_db = data.Role(role.id, xp_threshold, ctx.guild.id, currency_reward)
        db.set_role(role_db)
        cached.update_server_config(db.get_server(ctx.guild.id))
        await ctx.respond('Done')

@role.command(description="Remove a role from the list of automatic roles")
async def rm(ctx: commands.Context, role: discord.Role):
    if await is_mod(ctx):
        db.rm_role(role.id)
        cached.update_server_config(db.get_server(ctx.guild.id))
        await ctx.respond('Done')

@role.command(description="Show the list of automatic roles")
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        await info(ctx)