import discord
import asyncio
from discord.ext import commands
from data.databases.core.servers import (get_default_role)
from data.databases.core.db_management import (update_db, validate_server)
from Cogs.utils.decorators import timer
import json
import os
from typing import Optional, Literal


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.permissions = [
            "add_reactions", "administrator", "attach_files", "ban_members",
            "change_nickname", "connect", "create_events", "create_expressions",
            "create_instant_invite", "create_private_threads", "create_public_threads",
            "deafen_members", "embed_links", "external_emojis", "external_stickers",
            "kick_members", "manage_channels", "manage_emojis", "manage_emojis_and_stickers",
            "manage_events", "manage_expressions", "manage_guild", "manage_messages",
            "manage_nicknames", "manage_permissions", "manage_roles", "manage_threads",
            "manage_webhooks", "mention_everyone", "moderate_members", "move_members",
            "mute_members", "priority_speaker", "read_message_history", "read_messages",
            "request_to_speak", "send_messages", "send_messages_in_threads",
            "send_tts_messages", "send_voice_messages", "speak", "stream",
            "use_application_commands", "use_embedded_activities", "use_external_emojis",
            "use_external_sounds", "use_external_stickers", "use_soundboard",
            "use_voice_activation", "value", "view_audit_log", "view_channel",
            "view_creator_monetization_analytics"
        ]
        self.ld_permissions = [  # TODO make this abstract
            "send_messages",
            "create_public_threads",
            "create_private_threads",
            "send_messages_in_threads",
            "use_application_commands",
            "connect"
        ]

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None
    ) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    '''obtain a server's channel name store them in a json file for reference'''
    @commands.is_owner()
    @commands.command()
    async def channel_list(self, ctx: commands.Context, json_output: bool = False):
        channels = sorted(ctx.guild.channels, key=lambda x: x.position)
        channel_list = []
        for channel in channels:
            channel_list.append(channel.name)
        if json_output:
            with open("data/json/channel_list.json", "w") as f:
                json.dump(channel_list, f)
        return channel_list

    '''obtain a server's role name and id as key value pairs and store them in a json file for reference'''
    @commands.is_owner()
    @commands.command()
    async def role_id(self, ctx: commands.Context, json_output: bool = False):
        role_ids = []
        for role in ctx.guild.roles:
            role_ids.append([role.id, role.name, "role"])
        if json_output:
            with open("data/json/role_ids.json", "w") as f:
                json.dump(role_ids, f)
        return role_ids

    @commands.is_owner()
    @commands.command()
    async def member_id(self, ctx: commands.Context, json_output: bool = False):
        member_ids = []
        for member in ctx.guild.members:
            member_ids.append([member.id, member.name, "member"])
        if json_output:
            with open("data/json/member_ids.json", "w") as f:
                json.dump(member_ids, f)
        return member_ids

    async def amendPermsAllCategories(self, server, targets, amends, syncChannels):
        if server:
            for category in server.categories:  # Edit permissions for targets in the category
                for target in targets:
                    await category.set_permissions(target, **amends)

            # Optionally sync channels with their category
            if syncChannels:
                for channel in category.channels:
                    await channel.edit(sync_permissions=True)
            print('Permissions amended.')
        else:
            print('server not found.')

    '''clear all overrites for the specified target(s) in all channels of the server'''
    @commands.is_owner()
    @commands.command()
    @timer
    async def clear_all_permissions(self, ctx: commands.Context, *args: str):
        targets = await self.get_targets(ctx, *args)
        if not targets:
            return ctx.send('Aborting, no valid targets found...')

        # TODO DRY this
        for channel in (
            ctx.guild.text_channels
            + ctx.guild.voice_channels
            + ctx.guild.stage_channels
            + ctx.guild.categories
        ):
            for target in targets:
                await channel.set_permissions(target, overwrite=None)
        await ctx.send('Permissions cleared...')

        return ctx

    ''' amend permissions for the specified channel(s) (or channels of specified categories(s))
        for the specified target(s) with the specified permissions.

        # !bug: specifying categories applies ammends to categories alone and not their channels
    '''
    @commands.is_owner()
    @commands.command()
    @timer
    async def amend_permissions(self, ctx: commands.Context, *args: str):
        async def set_perms(ctx: commands.Context, channel):
            for target in targets:
                cur_perms = channel.overwrites_for(target)
                for perm in perms:
                    setattr(cur_perms, perm, perms[perm])
                await channel.set_permissions(target, overwrite=cur_perms)
            await ctx.send(f'Permissions set for channel {channel.mention}...')

        channels = []
        categories = []
        targets = []
        perms = {}
        for arg in args:
            if arg.isdigit():
                is_channel = ctx.guild.get_channel(int(arg))
                is_category = ctx.guild.get_channel(int(arg))
                is_target = ctx.guild.get_role(int(arg)) or ctx.guild.get_member(int(arg))
                if is_channel:
                    channels.append(is_channel)
                elif is_category:
                    categories.append(is_category)
                elif is_target:
                    targets.append(is_target)
            else:
                perm_val = arg.split("=")
                if perm_val[0] in self.permissions:
                    if perm_val[1] == "True":
                        perms[perm_val[0]] = True
                    else:
                        perms[perm_val[0]] = False

        for channel in channels:
            await set_perms(ctx, channel)
        for category in categories:
            for channel in category.text_channels + category.voice_channels + category.stage_channels:
                await set_perms(ctx, channel)

        return ctx

    '''sync permissions for the channel(s) of the specified categorie(s)'''
    @commands.is_owner()
    @commands.command()
    @timer
    async def sync_channels(self, ctx: commands.Context, *args: str):
        if not args:
            return await ctx.send('No categories specified to sync... Aborting')

        inputs = []
        for arg in args:
            if arg.isdigit():
                inputs.append(int(arg))

        categories = [category for category in ctx.guild.categories if category.id in inputs]
        if not categories:
            return await ctx.send('No valid categories found... Aborting')

        for category in categories:
            for channel in category.text_channels + category.voice_channels + category.stage_channels:
                await channel.edit(sync_permissions=True)
            await ctx.send(f'Permissions synced for category {category.name}...')

        return ctx

    '''can't use channel.overrites because it returns permissions in enumerish bit values.

       when storing permissions in json, we store only those that are set True or False,
       otherwise json size would be huge, crashing vs code. when we restore a backup,
       we set those not present in the json to None, so that they are not set to False/True
       and if the target is not present in the channel's overwrites, then we set the target's
       whole overwrite to None.
    '''
    @commands.is_owner()
    @commands.command()
    @timer
    async def perms_backup(self, ctx, path=None, *args):
        backup_file_path = path or f"data/json/backup/{ctx.guild.name}_perms_backup.json"
        await ctx.send("Taking backup of server's current perms state...")

        targets = list(ctx.guild.roles) + list(ctx.guild.members)
        json_data = {
                "server_id": ctx.guild.id,
                "server_name": ctx.guild.name,
                "perms": self.permissions,
                "targets": await self.role_id(ctx) + await self.member_id(ctx),
                "channels": []
            }
        for channel in (
            ctx.guild.text_channels
            + ctx.guild.voice_channels
            + ctx.guild.stage_channels
            + ctx.guild.categories
        ):
            json_channel = {
                        "channel_id": channel.id,
                        "channel_name": channel.name,
                        "channel_type": (
                            "text" if isinstance(channel, discord.TextChannel)
                            else "voice" if isinstance(channel, discord.VoiceChannel)
                            else "stage" if isinstance(channel, discord.StageChannel)
                            else "category"
                        )
                    }
            if channel.permissions_synced:
                json_channel["synced"] = [channel.category_id, channel.category.name]
            else:
                json_channel["synced"] = False

            json_channel["overwrites"] = []
            for target in targets:
                cur_perms = channel.overwrites_for(target)
                json_perms = {
                        "target_id": target.id,
                        "target_name": target.name,
                        "permissions": {}
                    }
                for perm in self.permissions:
                    try:
                        perm_value = getattr(cur_perms, perm)
                    except AttributeError:
                        continue
                    if perm_value is True or perm_value is False:
                        json_perms["permissions"][perm] = perm_value

                if json_perms["permissions"]:
                    json_channel["overwrites"].append(json_perms)
            if json_channel["overwrites"]:
                json_data["channels"].append(json_channel)

        with open(f"{backup_file_path}", "w") as f:
            json.dump(json_data, f)
        await ctx.send("Backup complete...")
        return ctx

    @commands.is_owner()
    @commands.group()
    async def databases(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid databases command passed...')

    '''sync the server's database with the server's current state'''
    @databases.command()
    @timer
    async def sync_server(self, ctx: commands.Context):
        await update_db(ctx, self.bot.db_pool, ctx.guild)
        await ctx.send('Server sync complete...')
        return ctx

    # !incomplete, not important, not urgent. careful when implementing
    @databases.command()
    async def flush(self, ctx: commands.Context, *args: str):
        if not args:
            return await ctx.send('No databases specified to flush...')

        for db in args:
            if db == "all":
                return await ctx.send('Flushing all tables...')
                # await flush_db_all(self.bot.db_pool, db, ctx.guild.id)

            else:
                await ctx.send(f'Flushing table {db}...')
            asyncio.sleep(1)
            # await flush_db(self.bot.db_pool, db, ctx.guild.id)

    # TODO permission checks
    @commands.is_owner()
    @commands.group(invoke_without_command=False)
    async def lockdown(self, ctx: commands.Context):

        if ctx.invoked_subcommand is None:
            # TODO implement default lockdown of context's channel
            await ctx.send('Invalid lockdown command passed...')

    '''
    lockdown the server for maintainance, all commands are disabled and only the owner can unlock the server.
    we create a json file to remember which channels had all read permissions removed for which roles so that
    we can retain the permissions when the server is unlocked
    '''
    @lockdown.command(name="maintainance")
    @timer
    async def lockdown_maintainance(self, ctx: commands.Context,  perms_backup=False, *args: str):
        if perms_backup == 'True' or perms_backup == 'true':
            backup_file_path = f"data/json/lockdowns/{ctx.guild.name}_perms_backup_maintainance_lockdown.json"
            await self.perms_backup(ctx, backup_file_path)
        else:
            await ctx.send('Backup not requested...')

        lockdown_file_path = f"data/json/lockdowns/{ctx.guild.name}_lockdown.json"
        if os.path.exists(lockdown_file_path):
            return await ctx.send('Server is currently in lockdown mode...\n Aborting')

        await ctx.send('Maintainance mode activated...\n All commands are disabled...\n')
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game('Maintainance mode...'))

        # TODO make this flexible
        await ctx.send('Initiating lockdown sequence...')
        targets = await self.get_targets(ctx, *args)
        if not targets:
            return

        # *locking channels and setting up json data to remember which channel perms to unlock
        await ctx.send('Locking down channels...')
        json_data = {
                "server_id": ctx.guild.id,
                "server_name": ctx.guild.name,
                "ld_permissions": self.ld_permissions,
                "targets": [target.id for target in targets],
                "channels": []
            }

        # TODO make this abstract
        for channel in (
            ctx.guild.text_channels
            + ctx.guild.voice_channels
            + ctx.guild.stage_channels
            + ctx.guild.categories
        ):
            if channel.permissions_synced:
                continue
            everyone_perms = channel.overwrites_for(ctx.guild.default_role)

            json_channel = {
                        "channel_id": channel.id,
                        "channel_name": channel.name,
                        "targets": []
                    }
            for target in targets:
                cur_perms = channel.overwrites_for(target)
                json_target = {
                        "target_id": target.id,
                        "target_name": target.name,
                        "permissions": {}
                    }

                '''if the target's channel is private and the target can't view the channel,
                    or if the target can't view the channel regardless of it's channel being private,
                    then skip the target
                '''
                if (
                    getattr(cur_perms, "view_channel") is False
                    or (
                        getattr(everyone_perms, "view_channel") is False
                        and getattr(cur_perms, "view_channel") is None
                    )
                ):
                    continue

                for ld_permission in self.ld_permissions:
                    try:
                        json_target["permissions"][ld_permission] = getattr(cur_perms, ld_permission)
                        setattr(cur_perms, ld_permission, False)
                    except AttributeError:
                        continue

                await channel.set_permissions(target, overwrite=cur_perms)
                if json_target["permissions"]:
                    json_channel["targets"].append(json_target)

            if json_channel["targets"]:
                json_data["channels"].append(json_channel)

        with open(f"{lockdown_file_path}", "w") as f:
            json.dump(json_data, f)
        await ctx.send('Lockdown sequence complete...\n\n Good luck when unlocking...')
        return ctx

    @commands.is_owner()
    @commands.group()
    async def unlock(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            # TODO implement default lockdown of context's channel
            await ctx.send('Invalid unlock command passed...')

    '''terminate the maintainance lockdown and unlock the server'''
    @unlock.command(name="maintainance")
    @timer
    async def unlock_maintainance(self, ctx: commands.Context, *args: str):
        lockdown_file_path = f"data/json/lockdowns/{ctx.guild.name}_lockdown.json"
        if not os.path.exists(lockdown_file_path):
            return await ctx.send('No lockdown file found for this server...\n Aborting')

        with open(lockdown_file_path, "r") as f:
            json_data = json.load(f)

        if json_data["server_id"] != ctx.guild.id:
            return await ctx.send('Lockdown file does not belong to this server...\n Aborting')

        await ctx.send('Terminating maintainance lockdown...')
        await ctx.send('Unlocking channels...')

        json_channels = json_data["channels"]
        if not json_channels:
            return await ctx.send('No channels found in lockdown file...\n Aborting')

        while json_channels:
            json_channel = json_channels.pop()
            channel = ctx.guild.get_channel(json_channel["channel_id"])
            json_targets = json_channel["targets"]

            while json_targets:
                json_target = json_targets.pop()
                target = ctx.guild.get_role(json_target["target_id"]) or ctx.guild.get_member(json_target["target_id"])
                cur_perms = channel.overwrites_for(target)

                json_permissions = json_target["permissions"]
                for permission, value in json_permissions.items():
                    setattr(cur_perms, permission, value)

                flag = False
                for permission in self.permissions:
                    try:
                        if getattr(cur_perms, permission) is True or getattr(cur_perms, permission) is False:
                            flag = True
                            break
                    except AttributeError:
                        continue
                if flag:
                    await channel.set_permissions(target, overwrite=cur_perms)
                else:
                    await channel.set_permissions(target, overwrite=None)

        await ctx.send('Unlock sequence complete...')
        os.remove(lockdown_file_path)
        await ctx.send('Maintainance lockdown terminated...')
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game('.help and your mom'))
        await ctx.send("Hoping perms aren't fu*ked.")
        return ctx

    @commands.command()
    async def get_targets(self, ctx: commands.Context, *args):
        if not args:
            await validate_server(self.bot.db_pool, ctx.guild)
            default_role = await get_default_role(self.bot.db_pool, ctx.guild.id)
            targets = [ctx.guild.get_role(int(default_role))]
            if not targets:
                await ctx.send('Aborting, no default role set for this server...')
            return targets
        else:
            targets = []
            for target in args:
                if target.isdigit():
                    target = ctx.guild.get_role(int(target)) or ctx.guild.get_member(int(target))
                    if target:
                        targets.append(target)

            if not targets:
                await ctx.send('Aborting, no valid targets found...')
                return None
            else:
                return targets


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
