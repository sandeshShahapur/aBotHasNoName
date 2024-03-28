'''''''''''''''''''''''''''''  USERS and SERVER_USERS  '''''''''''''''''''''''''''''''''
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

async def get_server_user(db_pool, server_id, user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                f"SELECT id FROM server_users where server_id = {server_id} AND user_id = {user_id}"
            )
        
async def set_server_user(db_pool, server_id, user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO server_users (server_id, user_id) VALUES ($1, $2) ON CONFLICT (server_id, user_id) DO NOTHING",
                server_id, user_id
            )