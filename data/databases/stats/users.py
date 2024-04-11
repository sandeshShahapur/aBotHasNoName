async def get_top_users(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                "SELECT user_id, COUNT(*) as message_count "
                "FROM messages "
                f"WHERE server_id = {server_id} "
                "GROUP BY user_id "
                "ORDER BY message_count DESC "
                "LIMIT 3"
            )


async def get_top_bumpers(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                "SELECT su.user_id, bu.count "
                "FROM server_users su "
                "INNER JOIN bump_counts bu ON su.id = bu.server_user_id "
                f"WHERE su.server_id = {server_id} "
                "ORDER BY bu.count DESC "
                "LIMIT 3"
            )
