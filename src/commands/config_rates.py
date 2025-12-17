from config import *

rate = config.create_subgroup('rate', "Manage XP rate")

@rate.command(description="Set the XP rate for text channel. Check documentation for more info")
async def text(ctx: commands.Context, base_xp_per_msg: int, cooldown_in_sec: int = 0, xp_factor: float = 1, min_xp: int = 1, rank_xp_threshold: int = -1):
    if await is_mod(ctx):
        db.set_xp_rate_text(ctx.guild.id, base_xp_per_msg, cooldown_in_sec, rank_xp_threshold, xp_factor, min_xp)
        cached.update_server_config(db.get_server(ctx.guild.id))
        await ctx.respond('Done')

@rate.command(description="Set the XP rate for voice channels")
async def voice(ctx: commands.Context, xp_per_minute: int):
    if await is_mod(ctx):
        db.set_xp_rate_voice(ctx.guild.id, xp_per_minute)
        cached.update_server_config(db.get_server(ctx.guild.id))
        await ctx.respond('Done')

@rate.command(description="Show the XP rate for text and voice channels")
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        server = cached.get_server(ctx.guild.id)
        embed = discord.Embed(
            title="XP rate",
            color=0x82c778,
        )
        add_xprate_fields(embed, server)
        await ctx.respond(embed=embed)