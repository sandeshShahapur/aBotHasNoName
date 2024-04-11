import discord
from discord.ext import commands, tasks
from Cogs.Plugins.PluginBase import plugin_disable, plugin_enable, set_config, view_config
from data.databases.core.db_management import (
                                validate_server,
                                validate_user,
                                validate_server_plugin,
                            )
from data.databases.Plugins.plugins import (
                                get_server_plugin,
                                get_server_plugin_config,
                            )
from data.databases.Plugins.bumper import (
                                bump,
                                bump_counts,
                                get_bump,
                                get_server_bump_count,
                                update_bump_reminder,
                                update_missed_reminder,
                                get_server_user_bump_count
                            )

from datetime import datetime, timedelta, timezone

from Cogs.utils.decorators import tolower


class Bumper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.modules = ["reminder", "miss_reminder", "counter"]
        self.bump_or_miss_reminder.start()

    def cog_unload(self):
        self.bump_or_miss_reminder.cancel()

    '''''''''''''''''''''''''''''''''PLUGIN COMMANDS'''''''''''''''''''''''''''''''''''
    @commands.is_owner()
    @commands.hybrid_group(name="bumper")
    async def bumper(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @bumper.command(name='view_config')
    @tolower
    async def bumper_view_config(self, ctx: commands.Context, module: str = None):
        await view_config(self, ctx, 'bumper', module)

    @commands.is_owner()
    @bumper.command(name='enable')
    @tolower
    async def bumper_enable(self, ctx: commands.Context, module: str):
        await plugin_enable(self, ctx, 'bumper', module)

    @commands.is_owner()
    @bumper.command(name='disable')
    @tolower
    async def bumper_disable(self, ctx: commands.Context, module: str):
        await plugin_disable(self, ctx, 'bumper', module)

    '''''''''''''''''''''''''''''''''MODULES COMMANDS'''''''''''''''''''''''''''''''''''
    # !commands that take input only work for slash commonds currently
    @commands.is_owner()
    @bumper.group()
    async def reminder(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @reminder.command(name='set_config')
    # !to_ping being default None will remove a ping role from the configuration. thus must provide a none value to remove the role. also provide the same for channel. # noqa
    async def breminder_set_config(
        self, ctx: commands.Context,
        channel: discord.TextChannel = None,
        to_ping: discord.Role = None
    ):
        channel = channel.id if channel else None
        to_ping = to_ping.id if to_ping else None
        await set_config(self, ctx, 'bumper', 'reminder', channel_id=channel, to_ping=to_ping)

    @commands.is_owner()
    @bumper.group()
    async def bump_miss_reminder(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @bump_miss_reminder.command(name='set_config')
    async def bmiss_reminder_set_config(
        self, ctx: commands.Context,
        channel: discord.TextChannel = None,
        interval: int = None,
        to_ping: discord.Role = None
    ):
        channel = channel.id if channel else None
        interval = interval + 7200 if interval else None
        to_ping = to_ping.id if to_ping else None

        await set_config(self, ctx, 'bumper', 'miss_reminder', channel_id=channel, interval=interval, to_ping=to_ping)

    '''''''''''''''''''''''''''''''ON BUMP EVENT'''''''''''''''''''''''''''
    @commands.Cog.listener('on_message')
    async def bump(self, message):
        if message.author == self.bot.user:
            return

        server_plugin = None
        if await validate_server(self.bot.db_pool, message.guild):
            server_plugin = await validate_server_plugin(
                self.bot.db_pool,
                message.guild,
                'bumper',
                validate_server_flag=True
            )
        if not server_plugin:
            server_plugin = await get_server_plugin(self.bot.db_pool, message.guild.id, 'bumper')

        if not server_plugin:
            self.bot.logger.error(f'Error: Server {message.guild.name} ({message.guild.id}) does not have the bumper plugin loaded.') # noqa
            return
        if not server_plugin['enabled']:
            return

        disboard = 302050872383242240
        if message.embeds and message.author.id == disboard and message.embeds[0].description.startswith('Bump done!'):
            if message.interaction:
                bumper_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
                if not bumper_config:
                    return self.bot.logger.error(f'Error: Server {message.guild.name} ({message.guild.id}) does not have a bumper configuration.') # noqa

                user = message.interaction.user
                server_user = await validate_user(self.bot.db_pool, message.guild, user.id, validate_server_flag=True)

                msg = ""
                if bumper_config["reminder"]["enabled"]:
                    should_miss_remind = True if bumper_config["miss_reminder"]["enabled"] else False
                    await bump(
                        self.bot.db_pool,
                        message.guild.id,
                        user.id, message.channel.id,
                        message.created_at,
                        True,
                        should_miss_remind
                    )
                    msg += bumper_config["reminder"]["bump_message"].format(user_mention=user.mention) + "\n"

                if bumper_config["counter"]["enabled"]:
                    if not server_user[0]:
                        self.bot.logger.error(f'Error: User {user.name} not found in database.')
                    else:
                        await bump_counts(self.bot.db_pool, server_user[0])
                        server_bcount = await get_server_bump_count(self.bot.db_pool, bumper_config['server_id'])
                        user_bcount = await get_server_user_bump_count(self.bot.db_pool, server_user[0])
                        msg += bumper_config["counter"]["bump_message"].format(
                            count=server_bcount, contribution_pct=round(user_bcount/server_bcount*100, 2))

                if msg:
                    await message.channel.send(msg)

    '''''''''''''''''''''''''''''''''BUMP REMINDER'''''''''''''''''''''''''''''''''''
    # TODO make efficient by considering only the servers that are in our bump database
    @tasks.loop(minutes=1.0)
    async def bump_or_miss_reminder(self):
        async def bg_task(module: str, module_remind: str):
            for guild in self.bot.guilds:
                server_plugin = await validate_server_plugin(
                    self.bot.db_pool,
                    guild,
                    'bumper',
                    validate_server_flag=True
                )
                if not server_plugin:
                    self.bot.logger.error(f'Error: Server {guild.name} ({guild.id}) does not have the bumper plugin loaded.') # noqa
                    continue
                if not server_plugin['enabled']:
                    continue

                bumper_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
                if not bumper_config:
                    self.bot.logger.error(f'Error: Server {guild.name} ({guild.id}) does not have a bumper configuration.') # noqa
                    continue
                if not bumper_config[module]["enabled"]:
                    continue

                previous_bump = await get_bump(self.bot.db_pool, guild.id)

                if (not previous_bump
                    or not previous_bump[module_remind]
                    or previous_bump['bumped_at']
                        + timedelta(seconds=bumper_config[module].get("interval", 7200))
                        > datetime.now(timezone.utc)
                ): # noqa
                    continue

                channel = (guild.get_channel(bumper_config[module]["channel_id"])
                           or guild.get_channel(previous_bump['channel_id']))
                to_ping = guild.get_role(bumper_config[module]["to_ping"]) or guild.get_member(previous_bump['user_id'])
                to_ping_mention = to_ping.mention if to_ping else "Unkown Role/Member"
                module_reminder = "reminder_message" if module == "reminder" else "message"
                reminder_message = bumper_config[module][module_reminder].format(to_ping_mention=to_ping_mention)

                if channel:
                    await channel.send(reminder_message)
                else:
                    self.bot.logger.error(f'Error: Channel {previous_bump["channel_id"]} not found in server {guild.name} ({guild.id}).') # noqa
                if module == "reminder":
                    await update_bump_reminder(self.bot.db_pool, guild.id, False)
                else:
                    await update_missed_reminder(self.bot.db_pool, guild.id, False)

        await bg_task("reminder", "should_remind")
        await bg_task("miss_reminder", "should_miss_remind")

    @bump_or_miss_reminder.before_loop
    async def before_bump_or_miss_reminder(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Bumper(bot))
