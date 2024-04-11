from discord.ext import commands

from Cogs.Plugins.PluginBase import plugin_disable, plugin_enable
from Cogs.utils.decorators import tolower


class Plugin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.plugins = ["Bumper", "Invite_Tracker"]

    @commands.is_owner()
    @commands.hybrid_group()
    async def plugin(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @plugin.command(name='enable')
    @tolower
    async def enable(self, ctx: commands.Context, plugin: str):
        if plugin not in [p.lower() for p in self.plugins]:
            return await ctx.send(f'{plugin} is not a valid plugin.')

        await plugin_enable(self, ctx, plugin, None)

    @commands.is_owner()
    @plugin.command(name='disable')
    @tolower
    async def disable(self, ctx: commands.Context, plugin: str):
        if plugin not in [p.lower() for p in self.plugins]:
            return await ctx.send(f'{plugin} is not a valid plugin.')

        await plugin_disable(self, ctx, plugin, None)


async def setup(bot):
    await bot.add_cog(Plugin(bot))
