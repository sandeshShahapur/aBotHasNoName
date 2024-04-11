# @client.event - to register an event
# async await - https://www.reddit.com/r/learnprogramming/comments/tya94m/comment/i3qy6ig/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content= # noqa
import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
import logging
import logging.handlers
from typing import List, Optional
from data.databases.core.servers import (
                                        get_prefix
                                    )
from data.databases.core.roles import (
                                delete_role
                            )
from data.databases.core.db_management import (
                                update_user_roles,
                                sync_user_roles,
                                update_db
                            )
import asyncpg


class aBotHasNoName(commands.Bot):
    db_pool: Optional[asyncpg.pool.Pool] = None
    initial_extensions: List[str] = []

    def __init__(
        self,
        *args,
        initial_extensions: List[str],
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        aBotHasNoName.initial_extensions = initial_extensions

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

        async def init_connection(connection):
            await connection.set_type_codec(
                    'json',
                    encoder=json.dumps,
                    decoder=json.loads,
                    schema='pg_catalog'
                )
        dsn = os.getenv('PROD_DATABASE_URL') if os.getenv('PROD') == 'True' else os.getenv('DEV_DATABASE_URL')
        db_pool = await asyncpg.create_pool(dsn=dsn, min_size=16, max_size=32, init=init_connection)
        aBotHasNoName.db_pool = db_pool

        # .loading extensions
        for extension in aBotHasNoName.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")
        print(f'{self.user} has setupped!')

    async def on_connect(self) -> None:
        print(f'{self.user} has connected to Discord!')

    async def on_ready(self) -> None:
        await self.change_presence(status=discord.Status.online, activity=discord.Game('.help and your mom'))
        print(f'{self.user} is ready!')

    async def on_disconnect(self) -> None:
        print(f'{self.user} has disconnected from Discord!')

    async def on_resumed(self) -> None:
        print(f'{self.user} has resumed connection in Discord!')
        await self.change_presence(status=discord.Status.online, activity=discord.Game('.help and your mom'))

    # TODO practically, would require permissions checks.
    # TODO add exception handling
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await update_db(aBotHasNoName.db_pool, guild)

    # !should not remove server from database, as it would remove all the users and their roles from the server.
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        pass

    async def on_member_join(self, member: discord.Member) -> None:
        '''
        # !musn't be enabled until the moderation plugin is implemented.
        # !other on_member_join events must wait until this is executed.

        await validate_server(aBotHasNoName.db_pool, member.guild)
        await set_user(aBotHasNoName.db_pool, member.id)

        # if the user has rejoined the server, then add the roles the user had before leaving the server.
        rejoined = await get_server_user(aBotHasNoName.db_pool, member.guild.id, member.id)
        if rejoined:
            guild_roles = member.guild.roles
            previous_member_roles_record = await get_server_user_roles(aBotHasNoName.db_pool, rejoined)
            previous_member_roles_id = [record['role_id'] for record in previous_member_roles_record]
            previous_member_roles = [role for role in guild_roles if role.id in previous_member_roles_id]
            await member.add_roles(*previous_member_roles, atomic=False)
        else:
            await set_server_user(aBotHasNoName.db_pool, member.guild.id, member.id)
        '''
        pass

    # !Should not remove user from database, as it would remove all the roles the user has in all the servers.
    # *This method is only called if the user is present in internal cache.
    async def on_member_remove(self, member: discord.Member) -> None:
        pass

    # !Should not remove user from database, as it would remove all the roles the user has in all the servers.
    # *This method is called instead of on_member_remove if the user is not in internal cache.
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent) -> None:
        if isinstance(payload.user, discord.Member):
            await sync_user_roles(aBotHasNoName.db_pool, payload.user, validate=True)

    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        # *role updates*
        # *add/remove the roles that have been added/removed
        await update_user_roles(aBotHasNoName.db_pool, after.guild, before, after)

    async def on_guild_role_delete(self, role: discord.Role) -> None:
        await delete_role(aBotHasNoName.db_pool, role.id)
        # TODO also do for role categories

    async def close(self) -> None:
        await super().close()
        print(f'{self.user} has logged out of and exited Discord!')
        await aBotHasNoName.db_pool.close()


def main() -> None:
    with open('config.json', 'r') as f:
        config = json.load(f)
        owner_id = config['owner_id']

    intents = discord.Intents.all()  # intent basically allows a bot to subscribe to specific buckets of events
    initial_extensions = ['Cogs.Stats', 'Cogs.Messages', 'Cogs.Configs', 'Cogs.Admin', 'Cogs.Roles',
                          'Cogs.Plugins.Plugin', 'Cogs.Plugins.InviteTracker', 'Cogs.Plugins.Bumper',
                          'Cogs.test.test']
    description = '''A bot that has no name'''

    bot = aBotHasNoName(
        initial_extensions=initial_extensions,
        command_prefix=get_prefix,
        intents=intents,
        description=description,
        owner_id=owner_id
    )

    load_dotenv()
    if os.getenv('PROD') == 'true':
        bot.run(os.getenv('PROD_TOKEN'))
    else:
        bot.run(os.getenv('DEV_TOKEN'))  # run bot


if __name__ == '__main__':
    main()
