import asyncio
import discord
from discord.ext import commands
from datetime import datetime
from data.databases.stats.servers import get_server
from data.databases.stats.roles import (
                                get_server_role_categories, 
                                get_server_role_category_id, 
                                get_roles_in_category,
                                set_role_category,
                                set_server_role_category_id,
                                delete_server_role_category_roles,
                                delete_server_role_category_id,
                                delete_role_category,
                                set_server_role_category_role,
                                delete_server_role_category_role
                            )
from data.databases.db_management import update_db


class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #TODO make this display the summary
    @commands.group(name="roles", invoke_without_command=False)
    async def roles(self, ctx):
        if not await get_server(self.bot.db_pool, ctx.guild.id):
            await update_db(self.bot.db_pool, ctx.guild)

        if ctx.invoked_subcommand is None:
            await ctx.reply("im here to help you with roles")

    

    '''''''''''''''''ROLES CATEGORY'''''''''''''''''''''
    @roles.group(name="categories")
    async def categories(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply("im here to help you with categories")

    @categories.command(name="ls")
    async def ls(self, ctx):
        categories = await get_server_role_categories(self.bot.db_pool, ctx.guild.id)
        if not categories:
            await ctx.reply("No categories found.")
            return
        else:
            message = "The categories are:"
            for i, category in enumerate(categories):
                message += f"\n \t{i+1}. **{category[0]}**\n"
                category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category[0])
                roles = await get_roles_in_category(self.bot.db_pool, category_id)
                for role in roles:
                    message += f"\n- {ctx.guild.get_role(role[0]).name}"
                message += "\n"
            await ctx.reply(message)

    @categories.command(name="create")
    async def create(self, ctx, category, *roles):
        if await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category):
            await ctx.reply("Category already exists.")
            return

        await set_role_category(self.bot.db_pool, category)
        await set_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        server_role_category = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        if not server_role_category:
            await ctx.reply("Category does not exist.")
            return

        await self.add_roles_to_server_category(ctx, server_role_category, roles)

    @commands.is_owner()
    @categories.command(name="delete")
    async def delete(self, ctx, category):
        server_role_category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        if not server_role_category_id:
            await ctx.reply("Category does not exist.")
            return

        await delete_server_role_category_roles(self.bot.db_pool, server_role_category_id)
        await delete_server_role_category_id(self.bot.db_pool, server_role_category_id)
        await ctx.reply(f"Category {category} has been deleted.")
        await delete_role_category(self.bot.db_pool, category)
    
    @commands.is_owner()
    @categories.command(name="add_roles")
    async def add_roles(self, ctx, category, *roles):
        server_role_category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        if not server_role_category_id:
            await ctx.reply("Category does not exist.")
            return

        await self.add_roles_to_server_category(ctx, server_role_category_id, roles)

    async def add_roles_to_server_category(self, ctx, server_role_category, roles):
        server_roles = [server_role.id for server_role in ctx.guild.roles]
        roles = [int(role) for role in roles if role.isdigit()]
        for role in roles:
            if role in server_roles:
                await set_server_role_category_role(self.bot.db_pool, server_role_category, role)
                await ctx.reply(f"Role {role} has been added to the category.")
            else:
                await ctx.reply(f"Role {role} does not exist in the server.")

    @commands.is_owner()
    @categories.command(name="remove_roles")
    async def remove_roles(self, ctx, category, *roles):
        server_role_category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        if not server_role_category_id:
            await ctx.reply("Category does not exist.")
            return

        server_roles = [server_role.id for server_role in ctx.guild.roles]
        roles = [int(role) for role in roles if role.isdigit()]
        for role in roles:
            if role in server_roles:
                await delete_server_role_category_role(self.bot.db_pool, server_role_category_id, role)
                await ctx.reply(f"Role {role} has been removed from the category.")
            else:
                await ctx.reply(f"Role {role} does not exist in the server.")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot)) 