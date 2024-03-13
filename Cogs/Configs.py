import discord
import asyncio
from discord.ext import commands
from data.databases.events import set_prefix, get_prefix, set_default_role, get_default_role
from typing import Union

class Configs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #TODO update the configs displayed, add permission checks
    @commands.is_owner()
    @commands.group()
    async def config(self, ctx):
        # .display the current server configurations
        if ctx.invoked_subcommand is None:
            prefix = await get_prefix(self.bot, ctx.message)
            role = await get_default_role(self.bot.db_pool, ctx.guild)

            title = "Server Configurations"
            description =   f"**Prefix**: {prefix}\n **Default Role**: {role.name if role else 'None'}"
            embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
            await ctx.send(embed=embed)

    @config.command()
    async def prefix(self, ctx, prefix):
        if len(prefix) > 5:
            await ctx.send("Prefix cannot be longer than 5 characters")
        else:
            await set_prefix(self.bot.db_pool, ctx.guild.id, prefix)
            await ctx.send(f"Prefix has been changed to {prefix}")

    #TODO add permission checks, fix potentioal bug with valid role name being a number
    @config.command()
    async def default_role(self, ctx, role: str = "None"):
        if role == "None":
            await ctx.send("No role provided, please provide a valid role")
            return

        roles = ctx.guild.roles
        if role.isdigit():
            role = discord.utils.get(roles, id=int(role))
        else:
            role = discord.utils.get(roles, name=role)
        if not role:
            await ctx.send("Role not found")
            return
        
        await set_default_role(self.bot.db_pool, ctx.guild.id, role.id)
        await ctx.send(f"Default role has been changed to {role.name}")

    

async def setup(bot: commands.Bot):
    await bot.add_cog(Configs(bot))