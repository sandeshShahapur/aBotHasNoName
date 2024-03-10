import asyncio
import discord
from discord.ext import commands
from datetime import datetime


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command()
    async def stats(self, ctx):
        pool = self.bot.db_pool

        async with pool.acquire() as connection:
            async with connection.transaction():
                query = f"SELECT user_id, COUNT(*) as message_count FROM messages_main where server_id = {str(ctx.guild.id)} GROUP BY user_id ORDER BY message_count DESC LIMIT 3"
                top_users = await connection.fetch(query)

                query = f"SELECT channel_id, COUNT(*) as message_count FROM messages_main where server_id = {str(ctx.guild.id)} GROUP BY channel_id ORDER BY message_count DESC LIMIT 3"
                top_channels = await connection.fetch(query)

        message = "**The top 3 users are:**\n"
        for i, user in enumerate(top_users):
            username = self.bot.get_user(user[0]).name
            message += f"{i+1}. {username} with {user[1]} messages.\n"

        message += "\n**The top 3 channels are:**\n"
        for i, channel in enumerate(top_channels):
            channelMention = self.bot.get_channel(channel[0]).mention
            message += f"{i+1}. {channelMention} with {channel[1]} messages.\n"
        
        initialDate = datetime.strptime('08-03-2024', '%d-%m-%Y').date()
        daysNum = (datetime.now().date() - initialDate).days
        message += f"\n\n Stats are produced from the previous {daysNum} days of data."

        await ctx.reply(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot)) 