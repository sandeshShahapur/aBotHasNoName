import discord
import asyncio
from discord.ext import commands
from data.databases.events import get_default_role
import json
import asyncpg


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ld_permissions = ["send_messages", "add_reactions", "create_public_threads", "create_private_threads", "send_messages_in_threads", "use_application_commands", "connect"] #TODO make this abstract

    #TODO permission checks
    @commands.is_owner()
    @commands.group()
    async def lockdown(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            #TODO implement default lockdown of context's channel
            await ctx.send('Invalid lockdown command passed...')

    @lockdown.command()
    async def maintainance(self, ctx: commands.Context,  *args: str): #users: discord.Member = None, roles: discord.Role = None,
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


    @commands.is_owner()
    @commands.group()
    async def unlock(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            #TODO implement default lockdown of context's channel
            await ctx.send('Invalid unlock command passed...')

        
    '''@unlock.command()
    async def maintainance(self, ctx: commands.Context, *args: str):
        if not args:
            default_role = await get_default_role(self.bot.db_pool, ctx.guild.id)
            targets = ctx.guild.get_role(default_role)
            if not targets:
                await ctx.send('Aborting, no default role set for this server...')
                return

            await ctx.send('Lockdown to terminate unspecified...')
        
        if args[0] == "maintainance":
            # *unlocking channels and setting up json data to remember which channel perms to lock
            await ctx.send('Terminating maintainance lockdown...')
            await ctx.send('Unlocking channels...')
            with open(f"data/json/lockdowns/{ctx.guild.name}_lockdown.json", "r") as f:
                json_data = json.load(f)

            for channel in ctx.guild.text_channels + ctx.guild.voice_channels:
                for 

            await ctx.send('Unlock sequence complete...')
            await ctx.send('Maintainance lockdown terminated...')
            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game('.help and your mom'))
            await ctx.send("Hoping perms aren't fu*ked.")'''
                

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