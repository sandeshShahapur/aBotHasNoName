import discord
import asyncio
from discord.ext import commands
from databases.events import get_default_role
import json

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #TODO permission checks
    @commands.is_owner()
    @commands.group()
    async def lockdown(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            #TODO implement default lockdown of context's channel
            await ctx.send('Invalid lockdown command passed...')

    @lockdown.command()
    async def maintainance(self, ctx: commands.Context, *args: str):
        await ctx.send('Maintainance mode activated...\n All commands are disabled...\n')
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game('Maintainance mode...'))
    
        # *these are the permissions that will be removed from the id's
        ld_permissions = ["send_messages", "add_reactions", "create_public_threads", "create_private_threads", "send_messages_in_threads", "use_application_commands", "connect"]
        if not args:
            targets = await get_default_role(self.bot.db_pool, ctx.guild.id)
            if not targets:
                await ctx.send('No default role set for this server...')
                return
        else: 
            targets = args
        targets = [ctx.guild.get_role(int(target)) for target in targets]

        # *locking channels and setting up json data to remember which channel perms to unlock    
        json_data = {}
        json_data['channels'] = {}
        for channel in ctx.guild.channels:
            json_channel = {f"{channel.id}": []}
            for target in targets:
                json_target = {f"{target.id}": []}
                cur_perms = channel.overwrites_for(target)
                for ld_permission in ld_permissions:
                    if ld_permission in cur_perms and cur_perms[ld_permission] == False:
                        # *channel is already locked, add to json
                        json_target[f"{target.id}"].append(ld_permission)
                    # *lock the channel permission
                    await channel.set_permissions(target, overwrite=discord.PermissionOverwrite(**{ld_permission: False}))
                if json_target[f"{target.id}"]:
                    json_channel[f"{channel.id}"].append(json_target)
            if json_channel[f"{channel.id}"]:
                json_data['channels'].update(json_channel)
        # *save json data if any channels were already locked
        if json_data['channels']:
            with open(f'{ctx.guild.name}_lockdown.json', 'w') as f:
                json.dump(json_data, f)
           
                


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))