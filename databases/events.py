import asyncpg, logging
import json

log = logging.getLogger('discord')

async def log_message(db_pool, message_id, server_id, user_id, channel_id, date, time):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO messages_main (message_id, server_id, user_id, channel_id, date, time) VALUES ($1, $2, $3, $4, $5, $6)",
                message_id, server_id, user_id, channel_id, date, time
            )
            #todo add logging to file
            #log.info(f'Logged message {message_id} from user {user_id} in server {server_id} in channel {channel_id} at {time} on {date}')

async def get_top_users(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT user_id, COUNT(*) as message_count FROM messages_main where server_id = {server_id} GROUP BY user_id ORDER BY message_count DESC LIMIT 3"
            )
        
async def get_top_channels(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT channel_id, COUNT(*) as message_count FROM messages_main where server_id = {server_id} GROUP BY channel_id ORDER BY message_count DESC LIMIT 3"
            )

async def bump(db_pool, server_id, user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            count = await connection.fetchval(
                f"SELECT count FROM bumps WHERE server_id = {server_id} AND user_id = {user_id}"
            )
            if not count:
                count = 1
                await connection.execute(
                    f"INSERT INTO bumps (server_id, user_id, count) VALUES ($1, $2, $3)",
                    server_id, user_id, count
                )
            else:
                count += 1
                await connection.execute(
                    f"UPDATE bumps SET count = {count} WHERE server_id = {server_id} AND user_id = {user_id}"
                )

            return count

#TODO add permission checks        
async def get_prefix(bot, message):
    db_pool = bot.db_pool
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            prefix = await connection.fetchval(
                f"SELECT prefix FROM servers where id = {message.guild.id}"
            )
            if prefix:
                return prefix
            else:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    return config['default_prefix']

#TODO add permission checks      
async def set_prefix(db_pool, server_id, prefix):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO servers (id, prefix) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET prefix = $2",
                server_id, prefix
            )

#TODO add permission checks    
async def get_default_role(db_pool, server):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            default_role = await connection.fetchval(
                f"SELECT default_role FROM servers where id = {server.id}"
            )
            return server.get_role(default_role) if default_role else None
        
#TODO add permission checks
async def set_default_role(db_pool, server_id, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO servers (id, default_role) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET default_role = $2",
                server_id, role_id
            )