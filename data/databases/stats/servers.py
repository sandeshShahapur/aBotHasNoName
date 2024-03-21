import json

async def set_server(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO servers (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
                server_id
            )

async def get_server(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow(
                f"SELECT * FROM servers where id = {server_id}"
            )

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
async def get_default_role(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                f"SELECT default_role FROM servers where id = {server_id}"
            )
        
#TODO add permission checks
async def set_default_role(db_pool, server_id, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO servers (id, default_role) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET default_role = $2",
                server_id, role_id
            )

async def setup_server(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO servers (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
                server_id
            )