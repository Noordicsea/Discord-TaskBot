import csv
import os
from datetime import datetime
from discord.ext import commands
from discord import app_commands
import discord
from discord.ui import View, Button

LOG_DIR = "data/logs"

def log_task(user_id, task, status):
    now = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(LOG_DIR, f"{now}_log.csv")
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["Timestamp", "User ID", "Task", "Status"])
        writer.writerow([datetime.now().isoformat(), user_id, task, status])

class ReminderButtons(View):
    def __init__(self, user_id, task):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.task = task

    @discord.ui.button(label="✅ Done", style=discord.ButtonStyle.success)
    async def done(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("Not your reminder!", ephemeral=True)
        log_task(self.user_id, self.task, "✅ Done")
        await interaction.response.send_message("✅ Logged as done!", ephemeral=True)
        self.disable_all_items()
        await interaction.message.edit(view=self)

    @discord.ui.button(label="❌ Skip", style=discord.ButtonStyle.danger)
    async def skip(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("Not your reminder!", ephemeral=True)
        log_task(self.user_id, self.task, "❌ Skipped")
        await interaction.response.send_message("❌ Logged as skipped!", ephemeral=True)
        self.disable_all_items()
        await interaction.message.edit(view=self)

class TasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stats", description="See your task completion stats")
    async def stats(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        done, skipped = 0, 0
        for file in os.listdir(LOG_DIR):
            if file.endswith(".csv"):
                with open(os.path.join(LOG_DIR, file), newline="") as f:
                    for row in csv.DictReader(f):
                        if row["User ID"] == uid:
                            if row["Status"] == "✅ Done": done += 1
                            elif row["Status"] == "❌ Skipped": skipped += 1
        total = done + skipped
        if total == 0:
            msg = "You haven't completed or skipped any tasks yet."
        else:
            percent = int((done / total) * 100)
            msg = f"You've completed {done}/{total} tasks ({percent}% success rate)."
        await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TasksCog(bot))