import discord
import asyncio
from discord.ext import commands
from data.databases.events import get_default_role
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
    async def maintainance(self, ctx: commands.Context,  *args: str): #users: discord.Member = None, roles: discord.Role = None,
        await ctx.send('Maintainance mode activated...\n All commands are disabled...\n')
        await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game('Maintainance mode...'))
    
        #TODO make this flexible
        await ctx.send('Initiating lockdown sequence...')
        # *these are the permissions that will be removed from the id's
        ld_permissions = ["send_messages", "add_reactions", "create_public_threads", "create_private_threads", "send_messages_in_threads", "use_application_commands", "connect"]
        #if not users and not roles:
        if not args:
            default_role = await get_default_role(self.bot.db_pool, ctx.guild.id)
            targets = ctx.guild.get_role(default_role)
            if not targets:
                await ctx.send('Aborting, no default role set for this server...')
                return
        else:
            #users, roles = users.split(','), roles.split(',')
            #targets = [ctx.guild.get_member(int(user)) for user in users] + [ctx.guild.get_role(int(role)) for role in roles]
            targets = [ctx.guild.get_member(int(member)) for member in args]

        await ctx.send('Locking down channels...')
        # *locking channels and setting up json data to remember which channel perms to unlock    
        json_data = {}
        json_data["channels"] = []
        for channel in ctx.guild.text_channels + ctx.guild.voice_channels: #TODO make this flexible
            json_channel = {
                            "channel_id": channel.id,
                            "targets": []
                            }
            for target in targets:
                json_target = {
                                "target_id": target.id,
                                "permissions": []
                                }
                cur_perms = channel.overwrites_for(target)
                for ld_permission in ld_permissions:
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
        # *save json data if any channels were already locked
        if json_data["channels"]:
            with open(f"data/json/lockdowns/{ctx.guild.name}_lockdown.json", "w") as f:
                json.dump(json_data, f)
        await ctx.send('Lockdown sequence complete...\n\n Good luck when unlocking...')
           
                


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))