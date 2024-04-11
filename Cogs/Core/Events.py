import datetime
from discord.ext import commands

from Cogs.Plugins.Invite_Tracker import Invite_Tracker, sync_invites
from data.databases.Plugins.invite_tracker import delete_invite, get_server_invites, set_invite
from data.databases.core.db_management import validate_server_plugin, validate_user
from data.databases.events.join_leaves import get_join, get_leave, set_join, set_leave


class Events (commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.join_leave_dependants = ["invite_tracker"]

    # *at least one of the dependants should be enabled for the event to be processed.
    async def should_process_event(self, server, dependants):
        for dependant in dependants:
            server_plugin = await validate_server_plugin(
                self.bot.db_pool, server, dependant, validate_server_flag=True
            )
            if not server_plugin:
                self.bot.logger.error(
                    f'Error: Plugin {dependant} for Server {server.name} ({server.id}) not found in database.'
                )
                continue
            if server_plugin["enabled"]:
                return True
        return False

    @commands.Cog.listener()
    async def on_member_join(self, member):
        '''Join and leave tables'''
        if self.should_process_event(member.guild, self.join_leave_dependants):
            # *find inviter
            server_invites = await member.guild.invites()
            server_invite_counts = {invite.code: invite.uses for invite in server_invites}
            db_invites = await get_server_invites(self.bot.db_pool, member.guild.id)

            potential_inviter, discrepant_inviters = []
            for db_invite in db_invites:
                count = server_invite_counts.get(db_invite['code'])
                if count is None:
                    await delete_invite(self.bot.db_pool, db_invite['code'])
                    continue

                if count != db_invite['uses']:
                    if count == db_invite['uses'] + 1:
                        potential_inviter.append([db_invite['created_by'], db_invite['code'], db_invite['uses']])
                    else:
                        discrepant_inviters.append(db_invite['code'])

            if len(potential_inviter) == 1 and not discrepant_inviters:
                await set_invite(self.bot.db_pool, potential_inviter[0]['code'], potential_inviter[0]['uses'] + 1)
                inviter_id = potential_inviter[0]['created_by']
            else:
                inviter_id = None

        user_id = await validate_user(self.bot.db_pool, member.guild, member.id)
        invite_code = potential_inviter[0]['code'] if len(potential_inviter) == 1 and not discrepant_inviters else None
        await set_join(self.bot.db_pool, inviter_id, user_id, invite_code, datetime.now(datetime.timezone.utc))

        if not inviter_id:
            await sync_invites(self.bot, member.guild)

        # Dependant Events
        if await self.should_process_event(member.guild, ["invite_tracker"]):
            await Invite_Tracker(self.bot).on_member_join(member)

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload):
        ''' If the corrosponding join was not found, set new join event and then set the leave event.
            If the corrosponding join was found, and it all ready has a leave event, do above.
            If the corrosponding join was found, and it does not have a leave event, set the leave event.
        '''
        guild = self.bot.get_guild(payload.guild_id)
        server_user = await validate_user(self.bot.db_pool, guild, payload.user.id)
        if server_user[0] is None:
            await self.bot.logger.error(
                f'Error: User {payload.user.id} not found in database for Server {guild.name} ({guild.id}).'
            )
            return

        async def set_get_join(server_user_id):
            await set_join(self.bot.db_pool, server_user_id, None, None, datetime.now(datetime.timezone.utc))
            return await get_join(self.bot.db_pool, server_user_id)

        if self.should_process_event(guild, self.join_leave_dependants):
            server_user = await validate_user(self.bot.db_pool, guild, payload.user.id)
            join_event = await get_join(self.bot.db_pool, server_user[0])
            if join_event is None:
                join_event = await set_get_join(server_user[0])

            leave_event = get_leave(self.bot.db_pool, join_event['id'])
            if leave_event:
                join_event = await set_get_join(server_user[0])

            await set_leave(self.bot.db_pool, join_event['id'], datetime.now(datetime.timezone.utc))

        # Dependant Events
        if await self.should_process_event(guild, ["invite_tracker"]):
            await Invite_Tracker(self.bot).on_member_remove(payload)
