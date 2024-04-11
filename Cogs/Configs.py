import discord
from discord.ext import commands
from data.databases.core.servers import (
                                    get_prefix,
                                    set_prefix,
                                    get_default_role,
                                    set_default_role
                                )
from data.databases.core.db_management import validate_server


class Configs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_default_role(self, ctx: commands.Context):
        role_id = await get_default_role(self.bot.db_pool, ctx.guild.id)
        return discord.utils.get(ctx.guild.roles, id=role_id) if role_id else None

    # TODO update the configs displayed, add permission checks
    @commands.is_owner()
    @commands.group()
    async def config(self, ctx):
        # .display the current server configurations
        if ctx.invoked_subcommand is None:
            prefix = await get_prefix(self.bot, ctx.message)
            role = await self.get_default_role(ctx)

            title = "Server Configurations"
            description = f"**Prefix**: {prefix}\n **Default Role**: {role.name if role else 'None'}"
            embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
            await ctx.send(embed=embed)

    # *validate the server before accessing any configs
    async def validation(self, server):
        await validate_server(self.bot.db_pool, server)

    @config.command()
    async def prefix(self, ctx, prefix=None):
        await self.validation(ctx.guild)
        if not prefix:
            return await ctx.send(f"Current prefix: {await get_prefix(self.bot, ctx.message)}")

        if len(prefix) > 5:
            await ctx.send("Prefix cannot be longer than 5 characters")
        else:
            await set_prefix(self.bot.db_pool, ctx.guild.id, prefix)
            await ctx.send(f"Prefix has been changed to {prefix}")

    # TODO add permission checks, fix potentioal bug with valid role name being a number
    @config.command()
    async def default_role(self, ctx, role: str = "None"):
        await self.validation(ctx.guild)
        if role == "None":
            role = await self.get_default_role(ctx)
            return await ctx.send("Default role is not set") if role else await ctx.send(f"Default role is {role.name}")

        roles = ctx.guild.roles
        if role.isdigit():
            role = discord.utils.get(roles, id=int(role))
        else:
            role = discord.utils.get(roles, name=role)
        if not role:
            return await ctx.send("Role not found")

        await set_default_role(self.bot.db_pool, ctx.guild.id, role.id)
        await ctx.send(f"Default role has been changed to {role.name}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Configs(bot))
