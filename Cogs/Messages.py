import discord
from discord.ext import commands
from databases.events import log_message
from utilities.datetime import convert_utc_to_ist

class Messages(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def process_messages(self, message: discord.Message) -> None:
        if message.author.bot or message.author == self.bot.user:
            return

        message_id = message.id
        server_id = message.guild.id
        channel_id = message.channel.id
        user_id = message.author.id
        datetime = convert_utc_to_ist(message.created_at)
        date = datetime.date()
        time = datetime.time()
        await log_message(self.bot.db_pool, message_id, server_id, user_id, channel_id, date, time)

async def setup(bot: commands.Bot):
    await bot.add_cog(Messages(bot)) 