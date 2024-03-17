import asyncio
import discord
from discord.ext import commands
from datetime import datetime
from data.databases.stats.servers import get_server, set_server
from data.databases.stats.users import get_top_users
from data.databases.stats.channels import get_top_channels
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


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #TODO make this display the summary
    @commands.group(name="stats")
    async def stats(self, ctx):
        if ctx.invoked_subcommand is None:
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

    async def common_validation(self, server):
        if not await get_server(self.bot.db_pool, server.id):
            await update_db(self.bot.db_pool, server)

    @stats.group(name="roles")
    async def roles(self, ctx):
        await self.common_validation(ctx.guild)

        if ctx.invoked_subcommand is None:
            await ctx.reply("im here to help you with roles")

    @roles.group(name="categories")
    async def categories(self, ctx):
        await self.common_validation(ctx.guild)

        if ctx.invoked_subcommand is None:
            await ctx.reply("im here to help you with categories")

    @categories.command(name="ls")
    async def ls(self, ctx):
        await self.common_validation(ctx.guild)

        categories = await get_server_role_categories(self.bot.db_pool, ctx.guild.id)
        if not categories:
            await ctx.reply("No categories found.")
            return
        else:
            message = "The categories are:"
            for category in categories:
                message += f"\n \t**{category[0]}**\n"
                category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category[0])
                roles = await get_roles_in_category(self.bot.db_pool, category_id)
                for role in roles:
                    message += f"\n- {ctx.guild.get_role(role[0]).name}"
            await ctx.reply(message)

    @categories.command(name="create")
    async def create(self, ctx, category, *roles):
        await self.common_validation(ctx.guild)

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

    @categories.command(name="delete")
    async def delete(self, ctx, category):
        await self.common_validation(ctx.guild)

        server_role_category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        if not server_role_category_id:
            await ctx.reply("Category does not exist.")
            return

        await delete_server_role_category_roles(self.bot.db_pool, server_role_category_id)
        await delete_server_role_category_id(self.bot.db_pool, server_role_category_id)
        await ctx.reply(f"Category {category} has been deleted.")
        await delete_role_category(self.bot.db_pool, category)
    
    @categories.command(name="add_roles")
    async def add_roles(self, ctx, category, *roles):
        await self.common_validation(ctx.guild)

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

    @categories.command(name="remove_roles")
    async def remove_roles(self, ctx, category, *roles):
        await self.common_validation(ctx.guild)

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
    await bot.add_cog(Stats(bot)) 