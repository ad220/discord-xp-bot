from config import *

channel = config.create_subgroup('channel', "Manage channels")

@channel.command(description="Add a channel to the list of channels to track")
async def add(ctx: commands.Context, channel: discord.TextChannel | discord.VoiceChannel):
    if await is_mod(ctx):
        db.add_channel(ctx.guild.id, channel.id, channel.type.value)
        cached.update_server_config(db.get_server(ctx.guild.id))
        if not is_channel_visible(ctx, channel.id):
            await ctx.respond(f"Warning: I cannot see <#{channel.id}>, please check my permissions")
        await ctx.respond('Done')

@channel.command(description="Remove a channel from the list of channels to track")
async def rm(ctx: commands.Context, channel: discord.TextChannel | discord.VoiceChannel):
    if await is_mod(ctx):
        db.rm_channel(channel.id)
        cached.update_server_config(db.get_server(ctx.guild.id))
        await ctx.respond('Done')

@channel.command(description="Show the list of channels to track")
async def show(ctx: commands.Context):
    if await is_mod(ctx):
        server = cached.get_server(ctx.guild.id)
        embed = discord.Embed(
            title="Channels",
            color=0x82c778,
        )
        add_channel_fields(embed, server)
        await ctx.respond(embed=embed)
        
        unavailable_channels = []
        for channel_id in server.channels['text'] + server.channels['voice']:
            if not is_channel_visible(ctx, channel_id):
                unavailable_channels.append(f"<#{channel_id}>")
        if unavailable_channels:
            await ctx.send(f"Warning: I cannot see the following channels {', '.join(unavailable_channels)}, please check my permissions")