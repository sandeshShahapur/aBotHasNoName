import asyncio
import discord
from discord.ext import commands
from datetime import datetime
from databases.events import get_top_users, get_top_channels


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # .display the top 3 users and channels
    @commands.command()
    async def stats(self, ctx):
        top_users = await get_top_users(self.bot.db_pool, ctx.guild.id)
        top_channels = await get_top_channels(self.bot.db_pool, ctx.guild.id)

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