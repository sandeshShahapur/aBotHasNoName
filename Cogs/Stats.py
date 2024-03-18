import asyncio
import discord
from discord.ext import commands
from datetime import datetime
from data.databases.stats.servers import get_server, set_server
from data.databases.stats.users import (
                                    get_top_users,
                                    get_top_bumpers
                                )
from data.databases.stats.channels import get_top_channels
from data.databases.stats.roles import (
                                get_server_role_category_id, 
                                get_roles_in_category,
                                get_role_count,
                                get_categories_of_role
                            )
from data.databases.db_management import update_db
from typing import Optional, Union


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    async def data_date_discretion(self) -> str:
        initialDate = datetime.strptime('08-03-2024', '%d-%m-%Y').date()
        daysNum = (datetime.now().date() - initialDate).days
        return f"\n\n Stats are produced from the previous {daysNum} days of data."

    #TODO make this display the summary
    @commands.group(name="stats", invoke_without_command=False)
    async def stats(self, ctx):
        if ctx.invoked_subcommand is None:
            top_users = await get_top_users(self.bot.db_pool, ctx.guild.id)
            top_channels = await get_top_channels(self.bot.db_pool, ctx.guild.id)

            message = "**The top 3 users are:**\n\n"
            for i, user in enumerate(top_users):
                username = (await self.bot.fetch_user(user[0])).name or "Unknown"
                message += f"{i+1}. **{username}** with **{user[1]}** messages.\n"

            message += "\n**The top 3 channels are:**\n"
            for i, channel in enumerate(top_channels):
                channelMention = self.bot.get_channel(channel[0]).mention or "Unknown"
                message += f"{i+1}.  **{channelMention}** with **{channel[1]}** messages.\n"
            
            message += await self.data_date_discretion()
            await ctx.send(message)

    '''''''''''''''''BUMPS STATS'''''''''''''''''''''
    @stats.group(invoke_without_command=False, name="bumps")
    async def stats_bumps(self, ctx):
        if ctx.invoked_subcommand is None:
            top_bumpers = await get_top_bumpers(self.bot.db_pool, ctx.guild.id)
            message = "**The top 3 bumpers are:**\n\n"
            for i, bumper in enumerate(top_bumpers):
                username = (await self.bot.fetch_user(bumper[0])).name or "Unknown"
                message += f"{i+1}.  **{username}** with **{bumper[1]}** bumps.\n"
            
            message += await self.data_date_discretion()
            await ctx.send(message)

    '''''''''''''''''ROLES STATS'''''''''''''''''''''
    @stats.group(invoke_without_command=False, name="roles")
    async def stats_roles(self, ctx, category: Optional[str], role: Optional[str]):
         # *assumning at most only one category and role is passed for now
        if ctx.invoked_subcommand is None:
            prison, sussy_baka = 953341678746480690, 1079122386995122236
            if category:
                if not category.isdigit():
                    category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
                    if not category_id:
                        await ctx.reply(f"Role category {category} does not exist.")
                        return
                else:
                    role = int(category)
            if role:
                server_roles = [server_role.id for server_role in ctx.guild.roles]
                if not role.isdigit() or int(role) not in server_roles:
                    await ctx.reply(f"Role {role} does not exist in server")
                    return
            
            # *if both a role and category are passed
            if category and role:
                await self.stats_of_role_in_category(ctx, category, role)

            # *if only a category is passed
            elif category:

                category_roles = [record["role_id"] for record in await get_roles_in_category(self.bot.db_pool, category_id)] 
                category_role_count = 0
                role_counts = []
                for i, role in enumerate(category_roles):
                    role_counts.append(await get_role_count(self.bot.db_pool, role))
                    category_role_count += role_counts[i]
                role_percentages = [(role_counts[i] / category_role_count) * 100 for i in range(len(category_roles))]

                message = f"Roles in category **{category}** are:\n"
                for i, role in enumerate(category_roles):
                    message += f"- Role **{ctx.guild.get_role(role).name}** has **{role_counts[i]}** members, which is **{role_percentages[i]:.{2}f}%** of the members.\n"
                await ctx.send(message)

            # *if only a role is passed
            elif role:
                categories = await get_categories_of_role(self.bot.db_pool, int(role))
                categories = [record[0] for record in categories]
                if not categories:
                    await ctx.reply(f"Role **{ctx.guild.get_role(int(role)).name}** does not exist in any category")
                    return
                await ctx.send(f"Role **{ctx.guild.get_role(int(role)).name}** is in categories **{categories}**")
                for category in categories:
                    await self.stats_of_role_in_category(ctx, category, role)

            # *if neither a role nor a category is passed
            else:
                server_roles = ctx.guild.roles
                server_roles_count = len(server_roles)
                member_count = ctx.guild.member_count
                prison_count = await get_role_count(self.bot.db_pool, prison)
                sussy_baka_count = await get_role_count(self.bot.db_pool, sussy_baka)
                average_role_count = member_count / server_roles_count

                message = f"Server {ctx.guild.name} has:\n **{member_count}** members\n **{server_roles_count}** roles \n **{average_role_count:.{2}f}** average roles per member\n\n **{prison_count}** members are in prison\n **{sussy_baka_count}** sussy bakas = **{sussy_baka_count/member_count*100:.{2}f}%** of members have not assigned themselves a role."
                await ctx.send(message)

    async def stats_of_role_in_category(self, ctx, category, role):
        category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        category_roles = [record["role_id"] for record in await get_roles_in_category(self.bot.db_pool, category_id)] 
        if not role.isdigit() or int(role) not in category_roles:
            await ctx.reply(f"Role {role} does not exist in category {category}")
            return
            
        role_count = await get_role_count(self.bot.db_pool, role)
        category_role_count = 0
        for rolz in category_roles:
            category_role_count += await get_role_count(self.bot.db_pool, rolz)
        role_percentage = (role_count / category_role_count) * 100

        await ctx.send(f"- Role **{ctx.guild.get_role(int(role)).name}** has **{role_count}** members in category **{category}**, which is **{role_percentage:.{2}f}%** of the members.\n")

async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot)) 