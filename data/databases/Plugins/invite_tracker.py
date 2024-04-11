''''''''''''''''''''''''''''  INVITES  '''''''''''''''''''''''''''''


# *use invite.code instead of invite.id because discord gateway only guarantees code to be filled.
async def set_invite(db_pool, invite_code, uses, created_by=None, created_at=None, server_id=None):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "INSERT INTO invites (code, created_by, uses, created_at, server_id) "
                "VALUES ($1, $2, $3, $4, $5) "
                "ON CONFLICT (code) DO UPDATE SET "
                "uses = $3, created_by = COALESCE(invites.created_by, $2)",
                invite_code, created_by, uses, created_at, server_id
            )


async def delete_invite(db_pool, invite_code):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "DELETE FROM invites WHERE code = $1",
                invite_code
            )


async def get_server_invites(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                "SELECT * FROM invites WHERE server_id = $1",
                server_id
            )
