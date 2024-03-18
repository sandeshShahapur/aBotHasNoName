async def get_user(db_pool, user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                f"SELECT user_id FROM users where id = {user_id}"
            )

async def set_user(db_pool, user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO users (id) VALUES ($1) ON CONFLICT (id) DO NOTHING",
                user_id
            )
async def set_server_user(db_pool, server_id, user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO server_users (server_id, user_id) VALUES ($1, $2) ON CONFLICT (server_id, user_id) DO NOTHING",
                server_id, user_id
            )

async def get_server_user(db_pool, server_id, user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                f"SELECT server_user_id FROM server_users where server_id = {server_id} AND user_id = {user_id}"
            )
        
async def get_top_users(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT user_id, COUNT(*) as message_count FROM messages_main where server_id = {server_id} GROUP BY user_id ORDER BY message_count DESC LIMIT 3"
            )
        
async def get_top_bumpers(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT su.user_id, bu.counts from server_users su INNER JOIN bumps bu ON su.server_user_id = bu.server_user_id where su.server_id = {server_id} ORDER BY bu.counts DESC LIMIT 3"
            )