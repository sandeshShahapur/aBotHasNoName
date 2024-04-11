import datetime
import discord
from discord.ext import commands

from data.databases.Plugins.plugins import get_server_plugin_config
from data.databases.core.db_management import validate_server, validate_server_plugin, validate_user
from data.databases.Plugins.invite_tracker import delete_invite, get_server_invites, set_invite
from Cogs.Plugins.PluginBase import plugin_disable, plugin_enable, set_config, view_config
from data.databases.core.users import get_user_from_server_user
from data.databases.events.join_leaves import get_invited_count, get_invited_leaves_count, get_join, set_join
from Cogs.utils.decorators import tolower


async def sync_invites(db_pool, server):
    await validate_server(db_pool, server)

    # *set or update invites present in the server which are or are not in the database.
    server_invites = await server.invites()
    for invite in await server_invites:
        invited_by = invite.inviter.id or -1
        server_user = await validate_user(db_pool, server, invited_by)
        await set_invite(db_pool, invite.code, server_user[0], invite.uses, invite.created_at, server.id)

    ''' delete invites present in the database which are not in the server.
        server_id is stored in the invites database to identify which server the invite belongs to
        when the invite creator is unknown, otherwise would have to check against all servers.
    '''
    server_invite_ids = [invite.code for invite in server_invites]
    db_invites = await get_server_invites(db_pool, server.id)
    for db_invite in db_invites:
        if db_invite['code'] not in server_invite_ids:
            await delete_invite(db_pool, db_invite['code'])


class Invite_Tracker(commands.Cog):
    def __init__(self, bot: commands.Bot, server: discord.Guild):
        self.bot = bot
        self.server = server
        self.modules = ["counter"]
        # self.bump_or_miss_reminder.start()

    def cog_unload(self):
        pass  # self.bump_or_miss_reminder.cancel()

    '''''''''''''''''''''''''''''''''PLUGIN COMMANDS'''''''''''''''''''''''''''''''''''
    @commands.is_owner()
    @commands.hybrid_group(name="invite_tracker")
    async def invite_tracker(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @invite_tracker.command(name='view_config')
    @tolower
    async def bumper_view_config(self, ctx: commands.Context, module: str = None):
        await view_config(self, ctx, 'invite_tracker', module)

    @commands.is_owner()
    @invite_tracker.command(name='enable')
    @tolower
    async def bumper_enable(self, ctx: commands.Context, module: str = None):
        await plugin_enable(self, ctx, 'invite_tracker', module)

    @commands.is_owner()
    @invite_tracker.command(name='disable')
    @tolower
    async def bumper_disable(self, ctx: commands.Context, module: str = None):
        await plugin_disable(self, ctx, 'invite_tracker', module)

    '''''''''''''''''''''''''''''''''MODULES COMMANDS'''''''''''''''''''''''''''''''''''
    @invite_tracker.command(name='set_config')
    async def invite_tracker_set_config(self, ctx: commands.Context, channel: discord.TextChannel):
        channel = channel.id or channel
        await set_config(self, ctx, 'invite_tracker', None, channel=channel)

    '''''''''''''''''''''''''''''''''GUILD INVITE EVENTS'''''''''''''''''''''''''''''''''''
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        created_by = await validate_user(self.bot.db_pool, invite.guild, invite.inviter.id) or -1

        await set_invite(
            self.bot.db_pool,
            invite.code,
            created_by,
            invite.uses,
            invite.created_at,
            invite.guild.id
        )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await delete_invite(self.bot.db_pool, invite.code)

    '''''''''''''''''''''''''''''''''USER JOIN/LEAVE EVENTS'''''''''''''''''''''''''''''''''''
    # !bug - currently does not handle inviters who have left the server.
    # TODO - integrate into plugin
    async def plugin_good(self, guild):
        server_plugin = await validate_server_plugin(
            self.bot.db_pool,
            guild,
            'invite_tracker',
            validate_server_flag=True
        )
        if not server_plugin:
            self.bot.logger.error(f'Error: Plugin invite_tracker for Server {guild.name} ({guild.id}) not found in database.')  # noqa
            return [False, None, None]
        if not server_plugin['enabled']:
            return [False, server_plugin, None]

        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        if not server_config:  # bug - will log error if plugin itself has no config
            self.bot.logger.error(f'Error: Plugin invite_tracker for Server {guild.name} ({guild.id}) does not have a configuration.') # noqa
            return [False, server_plugin, None]
        if not server_config['channel_id']:
            return [False, server_plugin, server_config]

        return [True, server_plugin, server_config]

    # *called after the on_member_join event in Cogs/Core/Events.py i.e. after join/leave tables are updated.
    async def on_member_join(self, member):
        plugin_good, server_plugin, server_config = await self.plugin_good(member.guild)
        if not plugin_good:
            return

        msg = server_config["join_message"].format(
                user=member.name,
                server_member_count=member.guild.member_count,
            )

        server_user = await validate_user(self.bot.db_pool, member.guild, member.id)
        join_event = get_join(self.bot.db_pool, server_user[0])
        if join_event['inviter_id'] is not None:
            inviter_user_id = await get_user_from_server_user(self.bot.db_pool, join_event['inviter_id'])
            try:
                inviter = await member.guild.fetch_member(inviter_user_id)
            except discord.errors.NotFound:
                inviter = None
            msg += server_config["inviter_resolved_message"].format(
                inviter=inviter.name if inviter else "Unknown"
            )
        else:
            msg += server_config["inviter_unresolved_message"]

        ''' if the counter module is enabled, then display the number of invites the user has.
            this requires usage of the join/leave events in database.
            join/leaves are required because discord invite stores total usage without accounting for leaves.
        '''
        if server_config['counter']['enabled']:
            if inviter is not None:
                msg += server_config["counter"]["known_join_message"].format(
                    invite_count=(
                        await get_invited_count(self.bot.db_pool, inviter.id)
                        - await get_invited_leaves_count(self.bot.db_pool, inviter.id)
                    )
                )
            else:
                msg += server_config["counter"]["invites_unresolved_message"].format(
                    unresolved_count="<not implemented yet>"
                )
        await member.guild.get_channel(server_config['channel_id']).send(msg)

    async def on_raw_member_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        server_good, server_plugin, server_config = await self.plugin_good(guild)
        if not server_good:
            return

        msg = server_config["leave_message"].format(
            user=payload.user.name,
            server_member_count=guild.member_count
        )

        if server_config['counter']['enabled']:
            server_user = await validate_user(self.bot.db_pool, guild, payload.user.id)
            join_event = get_join(self.bot.db_pool, server_user[0])
            if not join_event:  # TODO integrate into plugin
                await set_join(self.bot.db_pool, server_user[0], None, None, datetime.now(datetime.timezone.utc))
                join_event = await get_join(self.bot.db_pool, server_user[0])

            if join_event['inviter_id'] is not None:
                inviter_user_id = await get_user_from_server_user(self.bot.db_pool, join_event['inviter_id'])
                try:
                    inviter = await guild.fetch_member(inviter_user_id)
                except discord.errors.NotFound:
                    inviter = None

                msg += server_config["counter"]["known_leave_message"].format(
                    inviter=inviter.name if inviter else "Unknown",
                    invite_count=(
                        await get_invited_count(self.bot.db_pool, inviter.id)
                        - await get_invited_leaves_count(self.bot.db_pool, inviter.id)
                        if inviter else "<not implemented yet>"
                    )
                )
            else:
                msg += server_config["counter"]["unknown_leave_message"].format(
                    unresolved_count="<not implemented yet>"
                )

        await guild.get_channel(server_config['channel_id']).send(msg)


async def setup(bot):
    await bot.add_cog(Invite_Tracker(bot))
