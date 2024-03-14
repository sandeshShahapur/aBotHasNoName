import discord
import asyncio, asyncpg
from discord.ext import commands
from data.databases.events import (get_default_role,
                                   flush_db,
                                   flush_db_all)
import json
import os
import time


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ld_permissions = ["send_messages", "add_reactions", "create_public_threads", "create_private_threads", "send_messages_in_threads", "use_application_commands", "connect"] #TODO make this abstract

    @commands.is_owner()
    @commands.command()
    async def clearAllPermissions(self, ctx: commands.Context, *args: str):
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
    async def databases(self, ctx: commands.Context, *args: str):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid databases command passed...')

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
    @commands.group()
    async def lockdown(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            #TODO implement default lockdown of context's channel
            await ctx.send('Invalid lockdown command passed...')

    @lockdown.command(name="maintainance")
    async def lockdown_maintainance(self, ctx: commands.Context,  *args: str):
        start_time = time.time()
        
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

        with open(f"data/json/lockdowns/{ctx.guild.name}_lockdown.json", "w") as f:
            json.dump(json_data, f)
        await ctx.send('Lockdown sequence complete...\n\n Good luck when unlocking...')

        end_time = time.time()
        await ctx.send(f'\nLockdown sequence took {end_time - start_time} seconds to complete...')

    @commands.is_owner()
    @commands.group()
    async def unlock(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            #TODO implement default lockdown of context's channel
            await ctx.send('Invalid unlock command passed...')

        
    @unlock.command(name="maintainance")
    async def unlock_maintainance(self, ctx: commands.Context, *args: str):
        startTime = time.time()

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

                for ld_permission in ld_permissions:
                    if ld_permission not in json_permissions:
                        cur_perms = channel.overwrites_for(target)
                        setattr(cur_perms, ld_permission, True)
                        await channel.set_permissions(target, overwrite=cur_perms)

        await ctx.send('Unlock sequence complete...')
        os.remove(lockdown_file_path)
        await ctx.send('Maintainance lockdown terminated...')
        await self.bot.change_presence(status=discord.Status.online, activity=discord.Game('.help and your mom'))
        await ctx.send("Hoping perms aren't fu*ked.")

        endTime = time.time()
        await ctx.send(f'\nUnlock sequence took {endTime - startTime} seconds to complete...')
                

    async def get_targets(self, ctx: commands.Context, *args):
        if not args:
            default_role = await get_default_role(self.bot.db_pool, ctx.guild.id)
            targets = ctx.guild.get_role(default_role)
            if not targets:
                await ctx.send('Aborting, no default role set for this server...')
                return None
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