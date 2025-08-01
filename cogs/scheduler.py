import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from discord.ext import commands
from cogs.tasks import ReminderButtons

DATA_PATH = "data/reminders.json"

def load_reminders():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    return {}

async def send_reminder(bot, user_id, reminder):
    user = await bot.fetch_user(int(user_id))
    channel = bot.get_channel(reminder["channel_id"])
    if not channel:
        await user.send(f"⚠️ Reminder failed: Channel missing for `{reminder['title']}`")
        return
    checklist = "\n".join([f"• {item}" for item in reminder.get("checklist", [])])
    msg = f"🔔 **{reminder['title']}**\n{checklist}" if checklist else f"🔔 **{reminder['title']}**"
    await channel.send(msg, view=ReminderButtons(user_id, reminder['title']))

class SchedulerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler_task = None

    async def cog_load(self):
        self.scheduler_task = self.bot.loop.create_task(self.scheduler())

    async def cog_unload(self):
        if self.scheduler_task:
            self.scheduler_task.cancel()

    async def scheduler(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = datetime.now()
            check_time = now.strftime("%H:%M")
            weekday = now.strftime("%A")
            data = load_reminders()
            for uid, reminder_list in data.items():
                for r in reminder_list:
                    try:
                        r_time = datetime.strptime(r["time"], "%H:%M")
                        delay = int(r.get("delay", 0))
                        trigger_time = (r_time - timedelta(minutes=delay)).strftime("%H:%M")
                        if check_time == trigger_time and weekday in r["days"]:
                            await send_reminder(self.bot, uid, r)
                    except Exception as e:
                        logging.error(f"Error parsing reminder for {uid}: {e}")
            await asyncio.sleep(60 - datetime.now().second)

async def setup(bot):
    await bot.add_cog(SchedulerCog(bot))