import discord
import asyncio
from discord.ext import commands
from databases.events import get_default_role

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #TODO permission checks
    @commands.is_owner()
    @commands.group()
    async def lockdown(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            #TODO implement default lockdown of context's channel
            await ctx.send('Invalid lockdown command passed...')

    # 
    @lockdown.command()
    async def maintainance(self, ctx: commands.Context, *args: str):
        await ctx.send('Maintainance mode activated...\n All commands are disabled...\n')
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game('Maintainance mode...'))
    
        permissions = ["send_messages", "add_reactions", "create_public_threads", "create_private_threads", "send_messages_in_threads", "use_application_commands"]
        if not args:
            roles = await get_default_role(self.bot.db_pool, ctx.guild.id)
            if not roles:
                await ctx.send('No default role set for this server...')
                return
            
        for role in roles:
            


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))