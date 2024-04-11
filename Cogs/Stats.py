import discord
from discord.ext import commands
from data.databases.stats.users import (
                                    get_top_users,
                                    get_top_bumpers
                                )
from data.databases.stats.channels import get_top_channels
from data.databases.core.roles import (
                                get_server_role_category_id,
                                get_roles_in_category,
                                get_role_count,
                                get_categories_of_role
                            )
from data.data_visualisations.graph_templates.pie_chart import standard_pie_chart

from utils.embeds import create_embed
from datetime import datetime

import os


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def data_date_discretion(self) -> str:
        initialDate = datetime.strptime('08-03-2024', '%d-%m-%Y').date()
        daysNum = (datetime.now().date() - initialDate).days
        return f"\n\n Stats are produced from the previous {daysNum} days of data."

    # TODO make this display the summary
    @commands.group(name="stats", invoke_without_command=False)
    async def stats(self, ctx):
        if ctx.invoked_subcommand is None:
            top_users = await get_top_users(self.bot.db_pool, ctx.guild.id)
            top_channels = await get_top_channels(self.bot.db_pool, ctx.guild.id)

            message = "**The top 3 users are:**\n\n"
            for i, top_user in enumerate(top_users):
                user = self.bot.get_user(top_user[0])
                if not user:
                    try:
                        user = await self.bot.fetch_user(top_user[0])
                    except discord.errors.NotFound:
                        user = None
                username = user.name if user else "Unknown"
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
                user = self.bot.get_user(bumper[0])
                if not user:
                    try:
                        user = await self.bot.fetch_user(bumper[0])
                    except discord.errors.NotFound:
                        user = None
                username = user.name if user else "Unknown"

                message += f"{i+1}.  **{username}** with **{bumper[1]}** bumps.\n"

            message += await self.data_date_discretion()
            await ctx.send(message)

    '''''''''''''''''ROLES STATS'''''''''''''''''''''
    async def validate_category(self, ctx, category):
        if not category.isdigit():
            return await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        else:
            return False

    async def validate_role(self, ctx, role):
        if role.isdigit():
            server_roles = [server_role.id for server_role in ctx.guild.roles]
            return int(role) if int(role) in server_roles else False
        else:
            return False

    @stats.group(invoke_without_command=False, name="roles")
    async def stats_roles(self, ctx, *args):
        # *assumning at most only one category and role is passed for now
        if ctx.invoked_subcommand is None:
            prison, sussy_baka = 953341678746480690, 1079122386995122236
            category, role = None, None
            for arg in args:
                key_value = arg.split("=")
                if key_value[0] == "category":
                    category = key_value[1]
                    category_id = await self.validate_category(ctx, category)
                    if not category_id:
                        return await ctx.reply(f"Category {key_value[1]} does not exist.")

                elif key_value[0] == "role":
                    role = await self.validate_role(ctx, key_value[1])
                    if not role:
                        return await ctx.reply(f"Role {key_value[1]} does not exist.")

            # *if both a role and category are passed
            if category and role:
                await self.stats_of_role_in_category(ctx, category, role)

            # *if only a category is passed
            elif category:
                category_roles = [
                    record["role_id"]
                    for record in await get_roles_in_category(self.bot.db_pool, category_id)
                ]
                if not category_roles:
                    return await ctx.reply(f"Category **{category}** does not have any roles.")

                category_role_names = []
                category_role_counts = []
                sum_role_counts = 0
                for role in category_roles:
                    category_role_names.append(ctx.guild.get_role(role).name)
                    category_role_counts.append(await get_role_count(self.bot.db_pool, role))
                    sum_role_counts += category_role_counts[-1]

                # *create a pie chart and save it as an image
                filename = f'{ctx.guild.id}_{category}_roles_distribution.png'
                path = 'data/data_visualisations/stats_graphs'
                await standard_pie_chart(
                    values=category_role_counts,
                    names=category_role_names,
                    title=None,
                    path=path,
                    filename=filename
                )

                file = discord.File(path+filename, filename=filename)
                # *assumes each member has atmost one role in the category
                embed = await create_embed(
                    title=f"Roles demographics in {category}",
                    description=f'Sum total role assigns are **{sum_role_counts}**\n'
                                f'**{100-round(sum_role_counts/ctx.guild.member_count*100,2)}%** of members are unassigned', # noqa
                    image_url="attachment://" + filename,
                    footer=f"{self.bot.user.name} • Asked by {ctx.author.name}",
                    footer_icon_url=self.bot.user.avatar.url,
                    timestamp=True
                )
                await ctx.send(file=file, embed=embed)

                os.remove(path+filename)

            # *if only a role is passed
            elif role:
                categories = await get_categories_of_role(self.bot.db_pool, int(role))
                categories = [record[0] for record in categories]
                if not categories:
                    return await ctx.reply(f"Role **{ctx.guild.get_role(int(role)).name}** does not exist in any category") # noqa

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

                message = (
                    f"Server {ctx.guild.name} has:\n"
                    f"**{member_count}** members\n"
                    f"**{server_roles_count}** roles\n"
                    f"**{average_role_count:.{2}f}** average roles per member\n\n"
                    f"**{prison_count}** members are in prison\n"
                    f"**{sussy_baka_count}** sussy bakas ="
                    f" **{sussy_baka_count/member_count*100:.{2}f}%** of members have not assigned themselves a role."
                )
                await ctx.send(message)

    # TODO pie chart of this role vs all other roles in the category
    async def stats_of_role_in_category(self, ctx, category, role):
        category_id = await get_server_role_category_id(self.bot.db_pool, ctx.guild.id, category)
        category_roles = [record["role_id"] for record in await get_roles_in_category(self.bot.db_pool, category_id)]
        if not role.isdigit() or int(role) not in category_roles:
            return await ctx.reply(f"Role {role} does not exist in category {category}")

        role_count = await get_role_count(self.bot.db_pool, role)
        total_role_counts = 0
        for rolz in category_roles:
            total_role_counts += await get_role_count(self.bot.db_pool, rolz)
        role_percentage = (role_count / total_role_counts) * 100

        await ctx.send(
            f"- Role **{ctx.guild.get_role(int(role)).name}** has **{role_count}** members in"
            f" category **{category}**,"
            f" which is **{role_percentage:.{2}f}%** of the members.\n"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))
