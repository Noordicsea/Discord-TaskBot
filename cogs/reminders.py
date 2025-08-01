import json
import os
import csv
from datetime import datetime
from discord.ext import commands
from discord import app_commands
import discord
from discord.ui import Modal, TextInput, Select, View, Button

DATA_PATH = "data/reminders.json"
LOG_DIR = "data/logs"

class ReminderModal(Modal, title="Create a Reminder"):
    def __init__(self):
        super().__init__()
        self.title_input = TextInput(label="Reminder Title")
        self.time_input = TextInput(label="Time (24hr HH:MM)")
        self.checklist_input = TextInput(label="Checklist (comma separated or 'none')", required=False)
        self.delay_input = TextInput(label="Reminder Delay (minutes before)", placeholder="e.g. 5", required=False)
        self.add_item(self.title_input)
        self.add_item(self.time_input)
        self.add_item(self.checklist_input)
        self.add_item(self.delay_input)

    async def on_submit(self, interaction: discord.Interaction):
        delay_value = int(self.delay_input.value.strip()) if self.delay_input.value.strip().isdigit() else 0
        reminder_data = {
            "title": self.title_input.value,
            "time": self.time_input.value,
            "checklist": [] if self.checklist_input.value.lower() == "none" else [i.strip() for i in self.checklist_input.value.split(",")],
            "delay": delay_value,
            "channel_id": interaction.channel_id,
            "user_mention": True
        }
        await interaction.response.send_message("📅 Select the days:", view=DaySelectView(interaction.user.id, reminder_data), ephemeral=True)

class DaySelectView(View):
    def __init__(self, user_id, reminder_data):
        super().__init__(timeout=60)
        self.add_item(DaySelect(user_id, reminder_data))

class DaySelect(Select):
    def __init__(self, user_id, reminder_data):
        self.user_id = user_id
        self.reminder_data = reminder_data
        options = [discord.SelectOption(label=day, value=day) for day in
                   ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
        super().__init__(placeholder="Pick repeat days", options=options, min_values=1, max_values=7)

    async def callback(self, interaction: discord.Interaction):
        self.reminder_data["days"] = self.values
        data = load_reminders()
        data.setdefault(str(self.user_id), []).append(self.reminder_data)
        save_reminders(data)
        await interaction.response.send_message("✅ Reminder saved!", ephemeral=True)

class EditDaySelectView(View):
    def __init__(self, user_id, index, reminder_data):
        super().__init__(timeout=60)
        self.add_item(EditDaySelect(user_id, index, reminder_data))

class EditDaySelect(Select):
    def __init__(self, user_id, index, reminder_data):
        self.user_id = str(user_id)
        self.index = index
        self.reminder_data = reminder_data
        
        # Create options with current days pre-selected
        current_days = reminder_data.get("days", [])
        options = [
            discord.SelectOption(
                label=day, 
                value=day, 
                default=day in current_days
            ) for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        ]
        super().__init__(placeholder="Pick repeat days", options=options, min_values=1, max_values=7)

    async def callback(self, interaction: discord.Interaction):
        # Update the reminder data with new days
        self.reminder_data["days"] = self.values
        
        # Load current data and update the specific reminder
        data = load_reminders()
        user_reminders = data.get(self.user_id, [])
        
        if self.index >= len(user_reminders):
            return await interaction.response.send_message("⚠️ Reminder not found.", ephemeral=True)
        
        # Replace the reminder at the specified index
        user_reminders[self.index] = self.reminder_data
        save_reminders(data)
        
        await interaction.response.send_message("✅ Reminder updated!", ephemeral=True)

class EditReminderSelect(Select):
    def __init__(self, user_id, reminders):
        self.user_id = str(user_id)
        self.reminders = reminders
        options = [
            discord.SelectOption(label=r["title"], description=f"{r['time']} | {', '.join(r['days'])}", value=str(i))
            for i, r in enumerate(reminders)
        ]
        super().__init__(placeholder="Select a reminder to edit", options=options)

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        reminder = self.reminders[index]
        await interaction.response.send_modal(EditReminderModal(self.user_id, index, reminder))

class EditReminderModal(Modal, title="Edit Reminder"):
    def __init__(self, user_id, index, reminder):
        super().__init__()
        self.user_id = user_id
        self.index = index
        self.original_reminder = reminder

        self.title_input = TextInput(label="Title", default=reminder["title"])
        self.time_input = TextInput(label="Time (HH:MM)", default=reminder["time"])
        self.checklist_input = TextInput(label="Checklist (comma separated or 'none')", default=", ".join(reminder.get("checklist", [])), required=False)
        self.delay_input = TextInput(label="Delay (minutes before)", default=str(reminder.get("delay", 0)), required=False)

        self.add_item(self.title_input)
        self.add_item(self.time_input)
        self.add_item(self.checklist_input)
        self.add_item(self.delay_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Prepare updated reminder data
        updated_data = {
            "title": self.title_input.value,
            "time": self.time_input.value,
            "checklist": [] if self.checklist_input.value.lower() == "none" else [i.strip() for i in self.checklist_input.value.split(",")],
            "delay": int(self.delay_input.value) if self.delay_input.value.strip().isdigit() else 0,
            "channel_id": self.original_reminder.get("channel_id"),
            "user_mention": self.original_reminder.get("user_mention", True),
            "days": self.original_reminder.get("days", [])  # Keep existing days for now
        }
        
        # Show day selection with current days pre-selected
        await interaction.response.send_message("📅 Select the days:", view=EditDaySelectView(self.user_id, self.index, updated_data), ephemeral=True)

def load_reminders():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r") as f:
            return json.load(f)
    return {}

def save_reminders(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

class RemindersCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createreminder", description="Create a new reminder")
    async def createreminder(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReminderModal())

    @app_commands.command(name="listreminders", description="List your reminders")
    async def listreminders(self, interaction: discord.Interaction):
        data = load_reminders()
        reminders = data.get(str(interaction.user.id), [])
        if not reminders:
            await interaction.response.send_message("📭 No reminders found.", ephemeral=True)
        else:
            lines = [
                f"**{r['title']}** at {r['time']} on {', '.join(r['days'])} (⏱ {r.get('delay', 0)} min early)"
                for r in reminders
            ]
            await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="editreminder", description="Edit one of your reminders")
    async def editreminder(self, interaction: discord.Interaction):
        data = load_reminders()
        reminders = data.get(str(interaction.user.id), [])
        if not reminders:
            await interaction.response.send_message("📭 No reminders to edit.", ephemeral=True)
            return

        view = View()
        view.add_item(EditReminderSelect(interaction.user.id, reminders))
        await interaction.response.send_message("Select a reminder to edit:", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(RemindersCog(bot))