from globals import *
from utils.helpers import *

config = bot.create_group('config', "Manage bot configuration for this server")

@config.command(description="Show the full bot configuration for this server")
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        server = cached.get_server(ctx.guild.id)
        embed = discord.Embed(
            title="XP Bot configuration",
            color=0x82c778,
        )
        embed.add_field(name="Mod role", value=f"<@&{server.mod_role}>", inline=False)
        embed.add_field(name=" ", value="**=== Automatic roles ===**", inline=False)
        add_role_fields(embed, server)
        embed.add_field(name=" ", value="**=== Tracked channels ===**", inline=False)
        add_channel_fields(embed, server)
        embed.add_field(name=" ", value="**=== XP rates ===**", inline=False)
        add_xprate_fields(embed, server)
        await ctx.respond(embed=embed)



# Admin commands
@config.command()
async def mod_role(ctx: commands.Context, role: discord.Role):
    if ctx.author.guild_permissions.administrator:
        db.set_mod_role(ctx.guild.id, role.id)
        cached.update_server_config(db.get_server(ctx.guild.id))
        await ctx.respond('Done')
    else:
        await ctx.respond('You must be an administrator to use this command')