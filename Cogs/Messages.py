import discord
import asyncio
from discord.ext import commands
from data.databases.events import log_message
from utils.datetime import convert_utc_to_ist
from data.databases.events import set_server, set_user, set_server_user, get_server_user, bump
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
            datetime = convert_utc_to_ist(message.created_at)
            date = datetime.date()
            time = datetime.time()
            await log_message(self.bot.db_pool, message_id, server_id, user_id, channel_id, date, time)

        # *bump reminder
        disboard = 302050872383242240
        if message.embeds and message.author.id == disboard and message.embeds[0].description.startswith('Bump done!'):
            bumper = message.interaction.user
            server_user = await get_server_user(self.bot.db_pool, message.guild.id, bumper.id)
            if not server_user:
                await set_server(self.db_pool, message.guild.id)
                await set_user(self.db_pool, bumper.id)
                await set_server_user(self.db_pool, message.guild.id, bumper.id)
                server_user = await get_server_user(self.db_pool, message.guild.id, bumper.id)
            count = await bump(self.bot.db_pool, server_user)

            
            await message.channel.send(f'Thank you for bumping our server for the {count}th time!\n We will remind you in two hours to bump again.\n {bumper.mention}')
            
            reminder = await create_embed('It is time to bump the server again!', 'Bump our server by typing /bump!', color=discord.Color.green(), timestamp=True)
            await asyncio.sleep(7200)
            await message.channel.send(f'{bumper.mention}', embed=reminder)

async def setup(bot: commands.Bot):
    await bot.add_cog(Messages(bot)) 