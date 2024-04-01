import discord
import asyncio
from discord.ext import commands
from data.databases.message_handler import log_message
from utils.datetime import convert_utc_to_ist
from data.databases.servers import set_server
from data.databases.users import (
                                    set_user, 
                                    set_server_user, 
                                    get_server_user
                                    )
from data.databases.db_management import validate_user
from utils.embeds import create_embed

class Messages(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener('on_message')
    async def process_messages(self, message: discord.Message) -> None:
        if message.author == self.bot.user:
            return

        # .log message snowflakes
        if not message.author.bot:
            message_id = message.id
            server_id = message.guild.id
            channel_id = message.channel.id
            user_id = message.author.id
            sent_at = message.created_at
            await log_message(self.bot.db_pool, message_id, server_id, user_id, channel_id, sent_at)


async def setup(bot: commands.Bot):
    await bot.add_cog(Messages(bot)) 