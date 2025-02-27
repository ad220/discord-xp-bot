# This example requires the 'message_content' intent.

import discord
import os
import data

token = os.environ['DISCORD_TOKEN']

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
db = data.Database()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(token)


