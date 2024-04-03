import discord
from discord.ext import commands, tasks
from data.databases.db_management import (
                                validate_server,
                                validate_user,
                                validate_server_plugin,
                            )
from data.databases.plugins import (
                                bump,
                                bump_counts,
                                get_bump,
                                get_server_bump_count,
                                get_server_plugin,
                                get_server_plugin_config,
                                get_server_plugin_enabled,
                                get_server_user_bump_count,
                                set_server_plugin,
                                set_server_plugin_config,
                                update_bump_reminder,
                                update_missed_reminder
                            )
from data.databases.servers import set_server

import json
from datetime import datetime, timedelta

from utils.decorators import tolower

class Bumper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.modules = ["reminder", "miss_reminder", "counter"]
        self.bump_or_miss_reminder.start()

    def cog_unload(self):
        self.bump_or_miss_reminder.cancel()

    '''''''''''''''''''''''''''''''''PLUGIN COMMANDS'''''''''''''''''''''''''''''''''''
    @commands.is_owner()
    @commands.hybrid_group()
    async def bumper(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @bumper.command(name='view_config')
    async def bumper_view_config(self, ctx: commands.Context):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            return await ctx.send('bumper plugin not found in database.')

        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        await ctx.send(f' ```json\n{json.dumps(server_config, indent=4)}\n``` ')

    @commands.is_owner()
    @bumper.command(name='enable')
    @tolower
    async def bumper_enable(self, ctx: commands.Context, module: str):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            self.bot.logger.error(f'Error: Plugin bumper for Server {ctx.guild.name} ({ctx.guild.id}) not found in database.')

        if not server_plugin['enabled']:
            return await ctx.send('Please enable the bumper plugin first.')

        if module not in self.modules:
            return await ctx.send(f'{module} is not a valid module.')
            
        
        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        if server_config[module]["enabled"]:
            await ctx.send(f'{module} is already enabled.')
        else:
            server_config[module]["enabled"] = True
            await set_server_plugin_config(self.bot.db_pool, server_plugin['id'], server_config)
            await ctx.send(f'{module} has been enabled.')

    @commands.is_owner()
    @bumper.command(name='disable')
    @tolower
    async def bumper_disable(self, ctx: commands.Context, module: str):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            self.bot.logger.error(f'Error: Plugin bumper for Server {ctx.guild.name} ({ctx.guild.id}) not found in database.')

        if not server_plugin['enabled']:
            await ctx.send('Please enable the bumper plugin first.')

        if module not in self.modules:
            return await ctx.send(f'{module} is not a valid module.')
        
        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        if not server_config[module]["enabled"]:
            await ctx.send(f'{module} is already disabled.')
        else:
            server_config[module]["enabled"] = False
            await set_server_plugin_config(self.bot.db_pool, server_plugin['id'], server_config)
            await ctx.send(f'{module} has been disabled.')


    '''''''''''''''''''''''''''''''''MODULES COMMANDS'''''''''''''''''''''''''''''''''''
    @commands.is_owner()
    @bumper.group()
    async def reminder(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @reminder.command(name='view_config')
    async def breminder_view_config(self, ctx: commands.Context):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            ctx.send('bumper plugin not found in database.')

        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        await ctx.send(f' ```json\n{json.dumps(server_config["reminder"], indent=4)}\n``` ')

    @commands.is_owner()
    @reminder.command(name='set_config')
    async def breminder_set_config(self, ctx: commands.Context, channel: discord.TextChannel, to_ping: discord.Role, bump_message: str):
        #TODO implement DRY
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            self.bot.logger.error(f'Error: Plugin bumper for Server {ctx.guild.name} ({ctx.guild.id}) not found in database.')

        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        server_config['reminder']['channel_id'] = channel.id
        server_config['reminder']['to_ping_id'] = to_ping.id
        server_config['reminder']['bump_message'] = bump_message
        await set_server_plugin_config(self.bot.db_pool, server_plugin['id'], server_config)
        await ctx.send('Configuration has been set.')

    @commands.is_owner()
    @bumper.group()
    async def bump_miss_reminder(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @bump_miss_reminder.command(name='view_config')
    async def bmiiss_reminder_view_config(self, ctx: commands.Context):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            ctx.send('bumper plugin not found in database.')

        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        await ctx.send(f' ```json\n{json.dumps(server_config["miss_reminder"], indent=4)}\n``` ')

    @commands.is_owner()
    @bump_miss_reminder.command(name='set_config')
    async def bmiss_reminder_set_config(self, ctx: commands.Context, channel: discord.TextChannel, interval: int, to_ping: discord.Role):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            self.bot.logger.error(f'Error: Plugin bumper for Server {ctx.guild.name} ({ctx.guild.id}) not found in database.')

        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        server_config['miss_reminder']['channel_id'] = channel.id
        server_config['miss_reminder']['interval'] = interval
        server_config['miss_reminder']['to_ping_id'] = to_ping.id
        await set_server_plugin_config(self.bot.db_pool, server_plugin['id'], server_config)
        await ctx.send('Configuration has been set.')

    @commands.is_owner()
    @bumper.group()
    async def counter(self, ctx: commands.Context):
        pass

    @commands.is_owner()
    @counter.command(name='view_config')
    async def bcounter_view_config(self, ctx: commands.Context):
        server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            ctx.send('bumper plugin not found in database.')

        server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
        await ctx.send(f' ```json\n{json.dumps(server_config["counter"], indent=4)}\n``` ')
        

    '''''''''''''''''''''''''''''''''ON BUMP EVENT'''''''''''''''''''''''''''''''''''
    @commands.Cog.listener('on_message')
    async def bump(self, message):
        if message.author.bot:
            return
        
        server_plugin = None
        if await validate_server(self.bot.db_pool, message.guild):
            server_plugin = await validate_server_plugin(self.bot.db_pool, message.guild, 'bumper', validate_server_flag=True)
        if not server_plugin:
            server_plugin = await get_server_plugin(self.bot.db_pool, message.guild.id, 'bumper')
        
        if not server_plugin:
            self.bot.logger.error(f'Error: Server {message.guild.name} ({message.guild.id}) does not have the bumper plugin loaded.')
            return
        if not server_plugin['enabled']:
            return
        
        disboard = 302050872383242240
        if message.embeds and message.author.id == disboard and message.embeds[0].description.startswith('Bump done!'):
            if message.interaction:
                bumper_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
                if not bumper_config:
                    return self.bot.logger.error(f'Error: Server {message.guild.name} ({message.guild.id}) does not have a bumper configuration.')
                    

                user = message.interaction.user
                server_user = await validate_user(self.bot.db_pool, message.guild, user.id, validate_server_flag=False) #we recquire valid server_user

                message = ""
                if bumper_config["reminder"]["enabled"]:
                    should_miss_remind = True if bumper_config["missed_missed_reminder"]["enabled"] else False
                    await bump(self.bot.db_pool, message.guild.id, user.id, message.channel.id, message.created_at, True, should_miss_remind);
                    message += bumper_config["reminder"]["bump_message"].format(user_mention=user.mention) + "\n"

                if bumper_config["counter"]["enabled"]:
                    if not server_user[0]:
                        self.bot.logger.error(f'Error: User {user.name} not found in database.')
                    else:
                        await bump_counts(self.bot.db_pool, server_user[0])
                        server_bcount = await get_server_bump_count(self.bot.db_pool, bumper_config['server_id'])
                        user_bcount = await get_server_user_bump_count(self.bot.db_pool, server_user[0])
                        message += bumper_config["counter"]["bump_message"].format(count=server_bcount, contribution_pct=round(server_bcount/user_bcount*100, 2))

                if message:
                    await message.channel.send(message)

    '''''''''''''''''''''''''''''''''BUMP REMINDER'''''''''''''''''''''''''''''''''''
    #TODO make efficient by considering only the servers that are in our bump database
    @tasks.loop(minutes=1.0)
    async def bump_or_miss_reminder(self):
        async def bg_task(module: str, module_remind: str):
            for guild in self.bot.guilds:
                server_plugin = await validate_server_plugin(self.bot.db_pool, guild, 'bumper', validate_server_flag=True)
                if not server_plugin:
                    self.bot.logger.error(f'Error: Server {guild.name} ({guild.id}) does not have the bumper plugin loaded.')
                    continue
                if not server_plugin['enabled']:
                    continue

                bumper_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
                if not bumper_config:
                    self.bot.logger.error(f'Error: Server {guild.name} ({guild.id}) does not have a bumper configuration.')
                    continue
                if not bumper_config[module]["enabled"]:
                    continue

                previous_bump = await get_bump(self.bot.db_pool, guild.id)

                if (    not previous_bump or 
                        not previous_bump[module_remind] or 
                        previous_bump['bumped_at'] + timedelta(seconds=bumper_config[module].get("interval", 7200)) > datetime.now()
                    ):
                    continue

                channel = guild.get_channel(bumper_config[module]["channel_id"]) or guild.get_channel(previous_bump['channel_id'])
                to_ping = guild.get_role(bumper_config[module]["to_ping"]) or guild.get_member(previous_bump['user_id'])
                to_ping_mention = to_ping.mention if to_ping else "Unkown Role/Member"
                reminder_message = bumper_config[module]["reminder_message"].format(to_ping_mention=to_ping_mention)

                if channel:
                    await channel.send(reminder_message)
                else:
                    self.bot.logger.error(f'Error: Channel {previous_bump["channel_id"]} not found in server {guild.name} ({guild.id}).')
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