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

''''''''''''''''''''''''''''  INVITES  '''''''''''''''''''''''''''''
# *use invite.code instead of invite.id because discord gateway only guarantees code to be filled.
async def set_invite(db_pool, invite_code, server_user_id, uses, created_at):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO invites (code, server_user_id, uses, created_at) VALUES ($1, $2, $3, $4) ON CONFLICT (code) DO UPDATE SET uses = $3",
                invite_code, server_user_id, uses, created_at
            )

async def delete_invite(db_pool, invite_code):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"DELETE FROM invites WHERE code = $1",
                invite_code
            )