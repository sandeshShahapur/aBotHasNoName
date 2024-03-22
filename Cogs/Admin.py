import discord
import asyncio, asyncpg
from discord.ext import commands
from data.databases.stats.servers import (get_default_role)
from data.databases.db_management import (update_db, validate_server, flush_db, flush_db_all)
from utils.datetime import timer
import json
import os
import time


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.permissions = ['create_instant_invite', 'kick_members', 'ban_members', 'administrator', 'manage_channels', 'manage_guild', 'add_reactions', 'view_audit_log', 'priority_speaker', 'stream', 'read_messages', 'view_channel', 'send_messages', 'send_tts_messages', 'manage_messages', 'embed_links', 'attach_files', 'read_message_history', 'mention_everyone', 'external_emojis', 'use_external_emojis', 'view_guild_insights', 'connect', 'speak', 'mute_members', 'deafen_members', 'move_members', 'use_voice_activation', 'change_nickname', 'manage_nicknames', 'manage_roles', 'manage_permissions', 'manage_webhooks', 'manage_expressions', 'manage_emojis', 'manage_emojis_and_stickers', 'use_application_commands', 'request_to_speak', 'manage_events', 'manage_threads', 'create_public_threads', 'create_private_threads', 'send_messages_in_threads', 'external_stickers', 'use_external_stickers', 'use_embedded_activities', 'moderate_members', 'use_soundboard', 'use_external_sounds', 'send_voice_messages', 'create_expressions']
        self.ld_permissions = ["send_messages", "priority_speaker", "create_public_threads", "create_private_threads", "send_messages_in_threads", "use_application_commands", "connect"] #TODO make this abstract


    '''obtain a server's role name and id as key value pairs and store them in a json file for reference'''
    @commands.is_owner()
    @commands.command()
    async def json_role_id(self, ctx: commands.Context):
        role_ids = [[]]
        for role in ctx.guild.roles:
            role_ids.append([role.name, role.id])
        with open("data/json/role_ids.json", "w") as f:
            json.dump(role_ids, f)

    '''amend permissions for the specified channel(s) for the specified target(s) with the specified permissions'''
    @commands.is_owner()
    @commands.command()
    async def amend_permissions(self, ctx: commands.Context, *args: str):
        async def set_perms(ctx: commands.Context, channel: discord.TextChannel):
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


    '''sync permissions for the channel(s) of the specified categorie(s)'''
    @commands.is_owner()
    @commands.command()
    async def sync_channels(self, ctx: commands.Context, *args: str):
        if not args:
            await ctx.send('No categories specified to sync... Aborting')
            return
        
        inputs = []
        for arg in args:
            if arg.isdigit():
                inputs.append(int(arg))

        categories = [category for category in ctx.guild.categories if category.id in inputs]
        if not categories:
            await ctx.send('No valid categories found... Aborting')
            return
        
        for category in categories:
            for channel in category.text_channels + category.voice_channels + category.stage_channels:
                await channel.edit(sync_permissions=True)
            await ctx.send(f'Permissions synced for category {category.name}...')
        
    
    '''clear all overrites for the specified target(s) in all channels of the server'''
    @commands.is_owner()
    @commands.command()
    async def clear_all_permissions(self, ctx: commands.Context, *args: str):
        targets = await self.get_targets(ctx, *args)
        if not targets:
            ctx.send('Aborting, no valid targets found...')
            return

        for channel in ctx.guild.text_channels + ctx.guild.voice_channels:
            for target in targets:
                await channel.set_permissions(target, overwrite=None)
        await ctx.send('Permissions cleared...')


    @commands.is_owner()
    @commands.group()
    async def databases(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid databases command passed...')

    '''sync the server's database with the server's current state'''
    @databases.command()
    async def sync_server(self, ctx: commands.Context):
        await update_db(ctx, self.bot.db_pool, ctx.guild)
        await ctx.send('Server sync complete...')

    # !incomplete, not important, not urgent. careful when implementing
    @databases.command()
    async def flush(self, ctx: commands.Context, *args: str):
        if not args:
            await ctx.send('No databases specified to flush...')
            return
        for db in args:
            if db == "all":
                await ctx.send('Flushing all tables...')
                # await flush_db_all(self.bot.db_pool, db, ctx.guild.id)
                return
            else:
                await ctx.send(f'Flushing table {db}...')
            asyncio.sleep(1)
                # await flush_db(self.bot.db_pool, db, ctx.guild.id)

    #TODO permission checks
    @commands.is_owner()
    @commands.group(invoke_without_command=False)
    async def lockdown(self, ctx: commands.Context):

        if ctx.invoked_subcommand is None:
            #TODO implement default lockdown of context's channel
            await ctx.send('Invalid lockdown command passed...')

    '''
    lockdown the server for maintainance, all commands are disabled and only the owner can unlock the server.
    we create a json file to remember which channels had all read permissions removed for which roles so that
    we can retain the permissions when the server is unlocked
    '''
    @lockdown.command(name="maintainance")
    async def lockdown_maintainance(self, ctx: commands.Context,  *args: str):
        lockdown_file_path = f"data/json/lockdowns/{ctx.guild.name}_lockdown.json"
        if os.path.exists(lockdown_file_path):
            await ctx.send('Server is currently in lockdown mode...\n Aborting')
            return

        await ctx.send('Maintainance mode activated...\n All commands are disabled...\n')
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game('Maintainance mode...'))
    
        #TODO make this flexible
        await ctx.send('Initiating lockdown sequence...')
        targets = await self.get_targets(ctx, *args)
        if not targets:
            return

        # *locking channels and setting up json data to remember which channel perms to unlock    
        await ctx.send('Locking down channels...')
        json_data = {}
        json_data["targets"] = [target.id for target in targets]
        # *these are the permissions that will be removed from the id's
        json_data["ld_permissions"] = self.ld_permissions
        json_data["channels"] = []
        
        for channel in ctx.guild.text_channels + ctx.guild.voice_channels: #TODO make this abstract
            json_channel = {"channel_id": channel.id, "targets": []}

            for target in targets:
                json_target = {"target_id": target.id, "permissions": []}
                cur_perms = channel.overwrites_for(target)

                for ld_permission in self.ld_permissions:
                    if getattr(cur_perms, ld_permission) == False:
                        # *channel is already locked, add to json
                        json_target["permissions"].append(ld_permission)
                        continue

                    # *lock the channel permission
                    setattr(cur_perms, ld_permission, False)

                await channel.set_permissions(target, overwrite=cur_perms)
                if json_target["permissions"]:
                    json_channel["targets"].append(json_target)

            if json_channel["targets"]:
                json_data["channels"].append(json_channel)

        with open(f"{lockdown_file_path}", "w") as f:
            json.dump(json_data, f)
        await ctx.send('Lockdown sequence complete...\n\n Good luck when unlocking...')


    @commands.is_owner()
    @commands.group()
    async def unlock(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            #TODO implement default lockdown of context's channel
            await ctx.send('Invalid unlock command passed...')

    '''terminate the maintainance lockdown and unlock the server'''
    @unlock.command(name="maintainance")
    async def unlock_maintainance(self, ctx: commands.Context, *args: str):
        lockdown_file_path = f"data/json/lockdowns/{ctx.guild.name}_lockdown.json"
        if not os.path.exists(lockdown_file_path):
            await ctx.send('No lockdown file found for this server...\n Aborting')
            return
        with open(lockdown_file_path, "r") as f:
            json_data = json.load(f)
        
        # *unlocking channels and setting up json data to remember which channel perms to lock
        await ctx.send('Terminating maintainance lockdown...')
        ld_permissions = json_data["ld_permissions"]
        targets = [ctx.guild.get_role(target) or ctx.guild.get_member(target) for target in json_data["targets"]]
        await ctx.send('Unlocking channels...')

        # *unlocking channels for targets of permissions that are not present in json i.e. retaining the prior locked channels before the lockdown
        json_channels = json_data["channels"]
        for channel in ctx.guild.text_channels + ctx.guild.voice_channels:
            channel_present = json_channels and channel.id in [json_channel["channel_id"] for json_channel in json_channels]
            if channel_present:
                json_targets = [json_target for json_channel in json_channels if json_channel["channel_id"] == channel.id for json_target in json_channel["targets"]]
            else:
                json_targets = []

            for target in targets:
                target_present = json_targets and target.id in [json_target["target_id"] for json_target in json_targets]
                if target_present:
                    json_permissions = [json_permission for json_target in json_targets if json_target["target_id"] == target.id for json_permission in json_target["permissions"]]
                else:
                    json_permissions = []

                cur_perms = channel.overwrites_for(target)
                for ld_permission in ld_permissions:
                    if ld_permission not in json_permissions:
                        setattr(cur_perms, ld_permission, True)
                await channel.set_permissions(target, overwrite=cur_perms)

        await ctx.send('Unlock sequence complete...')
        os.remove(lockdown_file_path)
        await ctx.send('Maintainance lockdown terminated...')
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game('.help and your mom'))
        await ctx.send("Hoping perms aren't fu*ked.")

                
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