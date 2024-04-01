from discord.ext import commands

from data.databases.db_management import validate_server_plugin
from data.databases.plugins import get_server_plugin_enabled, set_server_plugin_enabled


class Plugin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.plugins = ["Bumper"]

    @commands.is_owner()
    @commands.hybrid_group()
    async def plugin(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @plugin.command(name='plugin_enable')
    async def enable(self, ctx: commands.Context, plugin: str):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, plugin, validate_server_flag=True)
        if await set_server_plugin_enabled(self.bot.db_pool, ctx.guild.id, plugin):
            return await ctx.send(f'{plugin} is already enabled in this server.')
        else:
            await set_server_plugin_enabled(self.bot.db_pool, server_plugin['id'], True)
            await ctx.send(f'{plugin} has been enabled in this server.')
    
    @commands.is_owner()
    @plugin.command(name='plugin_disable')
    async def disable(self, ctx: commands.Context, plugin: str):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, plugin, validate_server_flag=True)
        if not await get_server_plugin_enabled(self.bot.db_pool, ctx.guild.id, plugin):
            return await ctx.send(f'{plugin} is already disabled in this server.')
        else:
            await set_server_plugin_enabled(self.bot.db_pool, server_plugin['id'], False)
            await ctx.send(f'{plugin} has been disabled in this server.')

async def setup(bot):
    await bot.add_cog(Plugin(bot))