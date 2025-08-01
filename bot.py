import os
import logging
from dotenv import load_dotenv
import discord
from discord.ext import commands

# === SETUP ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_DIR = "data/logs"
os.makedirs("data", exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# === LOGGING ===
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "bot.log"),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# === BOT ===
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class ReminderBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Load all cogs
        await self.load_extension("cogs.reminders")
        await self.load_extension("cogs.tasks")
        await self.load_extension("cogs.scheduler")
        
        await self.tree.sync()
        logging.info("Bot is ready and commands synced.")

bot = ReminderBot()

# === RUN ===
@bot.event
async def on_ready():
    print(f"\u2705 Logged in as {bot.user} (ID: {bot.user.id})")

bot.run(TOKEN)
