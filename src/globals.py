import discord
import data

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = discord.Bot(intents=intents)
db = data.Database()
cached = data.Cache()
