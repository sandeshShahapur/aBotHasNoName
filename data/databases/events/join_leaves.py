'''''''''''''''''''''''''''''''''JOINS'''''''''''''''''''''''''''''''''''
async def set_join(db_pool, server_user_id, inviter_id, invite_code, joined_at): # noqa
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "INSERT INTO join_events (server_user_id, inviter_id, invite_code, joined_at) "
                "VALUES ($1, $2, $3, $4)",
                server_user_id, inviter_id, invite_code, joined_at
            )


async def get_join(db_pool, server_user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            join_event_rows = await connection.fetch(
                "SELECT * FROM join_events WHERE server_user_id = $1"
                " ORDER BY joined_at DESC"
                " LIMIT 1",
                server_user_id
            )
            return join_event_rows[0] if join_event_rows else None


async def get_invited_count(db_pool, inviter_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                "SELECT COUNT(*) FROM join_events WHERE inviter_id = $1",
                inviter_id
            )


'''''''''''''''''''''''''''''''''LEAVES'''''''''''''''''''''''''''''''''''
async def set_leave(db_pool, join_id, left_at): # noqa
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "INSERT INTO leave_events (join_id, left_at) VALUES ($1, $2)",
                join_id, left_at
            )


async def get_leave(db_pool, join_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow(
                "SELECT * FROM leave_events WHERE join_id = $1",
                join_id
            )


async def get_invited_leaves_count(db_pool, inviter_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                "SELECT COUNT(*) FROM join_events INNER JOIN leave_events "
                " ON join_events.id = leave_events.join_id"
                " WHERE join_events.inviter_id = $1",
                inviter_id
            )
