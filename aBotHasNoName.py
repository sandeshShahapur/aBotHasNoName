# @client.event - to register an event
# async await - https://www.reddit.com/r/learnprogramming/comments/tya94m/comment/i3qy6ig/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
import asyncio
import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
import logging, logging.handlers
from typing import List, Optional
from databases.events import (
                                get_prefix,
                                set_server,
                                set_user,
                                set_server_user,
                                set_server_user_role,
                                get_server_user,
                                get_server_user_roles,
                                delete_role,
                                delete_user_role
                            )

import asyncpg

load_dotenv("main.env")
class aBotHasNoName(commands.Bot):
    def __init__(
        self,
        *args,
        initial_extensions: List[str],
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.initial_extensions = initial_extensions

    # .all bot settings and configurations should be done here.
    async def setup_hook(self) -> None:
        await super().setup_hook()
        print(f'{self.user} has logged in!')

        logger = logging.getLogger('discord')
        logger.setLevel(logging.INFO)

        handler = logging.handlers.RotatingFileHandler(
            filename='discord.log',
            encoding='utf-8',
            maxBytes=32 * 1024 * 1024,  # 32 MiB
            backupCount=5,  # Rotate through 5 files
        )
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        
        db_pool = await asyncpg.create_pool(dsn=os.getenv('DATABASE_URL'), min_size=16, max_size=32)
        self.db_pool = db_pool

        # .loading extensions
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")


        print(f'{self.user} has setupped!')

    async def on_connect(self) -> None:
        print(f'{self.user} has connected to Discord!')

    async def on_ready(self) -> None:
        print(f'{self.user} is ready!')

    async def on_disconnect(self) -> None:
        print(f'{self.user} has disconnected from Discord!')

    async def on_resumed(self) -> None:
        print(f'{self.user} has resumed connection in Discord!')

    #TODO practically, would require permissions checks.
    #TODO add exception handling    
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await set_server(self.db_pool, guild.id)

        # .loading all the present users and their roles in the server to the database.
        users = guild.members
        for user in users:
            await set_user(self.db_pool, user.id)
            await set_server_user(self.db_pool, guild.id, user.id)

            server_user = await get_server_user(self.db_pool, guild.id, user.id)
            if server_user:
                roles = user.roles
                for role in roles:
                    await set_server_user_role(self.db_pool, server_user, role.id)

    # !should not remove server from database, as it would remove all the users and their roles from the server.
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        pass

    async def on_member_join(self, member: discord.Member) -> None:
        await set_user(self.db_pool, member.id)
        
        #.if the user has rejoined the server, then add the roles the user had before leaving the server.'''
        rejoined = await get_server_user(self.db_pool, member.guild.id, member.id)
        if rejoined:
            guild_roles = member.guild.roles
            previous_member_roles_id = get_server_user_roles(self.db_pool, rejoined)
            previous_member_roles = [role for role in guild_roles if role.id in previous_member_roles_id]
            member.add_roles(*previous_member_roles, atomic=False)
        else:
            await set_server_user(self.db_pool, member.guild.id, member.id)

    # !Should not remove user from database, as it would remove all the roles the user has in all the servers.
    # *This method is only called if the user is present in internal cache.
    async def on_member_remove(self, member: discord.Member) -> None:
        pass

    # !Should not remove user from database, as it would remove all the roles the user has in all the servers.
    # *This method is called instead of on_member_remove if the user is not in internal cache.
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent) -> None:
        pass

    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        # .role updates
        server_user = await get_server_user(self.db_pool, after.guild.id, after.id)
        deleted_roles = list(set(before.roles) - set(after.roles))
        added_roles = list(set(after.roles) - set(before.roles))
        for role in deleted_roles:
            await delete_user_role(self.db_pool, server_user, role.id)
        for role in added_roles:
            await set_server_user_role(self.db_pool, server_user, role.id)

    async def on_guild_role_delete(self, role: discord.Role) -> None:
        await delete_role(self.db_pool, role.guild.id, role.id)

    async def close(self) -> None:
        await super().close()
        print(f'{self.user} has logged out of and exited Discord!')
        await self.db_pool.close()

        
def main() -> None:
    with open('config.json', 'r') as f:
        config = json.load(f)
        owner_id = config['owner_id']

    intents = discord.Intents.all() #intent basically allows a bot to subscribe to specific buckets of events
    initial_extensions = ['Cogs.Stats', 'Cogs.Messages', 'Cogs.Configs']
    description = '''A bot that has no name'''

    bot = aBotHasNoName(
        initial_extensions=initial_extensions,
        command_prefix=get_prefix,
        intents=intents,
        description=description,
        owner_id=owner_id
    ) 
    bot.run(os.getenv('TOKEN')) #run bot

if __name__ == '__main__':
    main()