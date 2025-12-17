import datetime
from discord.ext import tasks

from globals import *

@tasks.loop(time=datetime.time(hour=5, minute=0, tzinfo=datetime.timezone.utc))
async def daily_tasks():
    print("executing daily tasks")
    # History entry
    server_list = db.get_servers()
    for server_id in server_list:
        users = db.get_users(server_id)
        db.add_history_records(server_id, users)

    data.backup_database()

@daily_tasks.before_loop
async def before_backup():
    """Attend que le bot soit prêt avant de démarrer la tâche"""
    await bot.wait_until_ready()