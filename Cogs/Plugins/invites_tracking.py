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