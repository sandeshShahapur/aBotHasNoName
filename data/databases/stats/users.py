async def get_top_users(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT user_id, COUNT(*) as message_count FROM messages where server_id = {server_id} GROUP BY user_id ORDER BY message_count DESC LIMIT 3"
            )
        
async def get_top_bumpers(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT su.user_id, bu.count from server_users su INNER JOIN bumps bu ON su.id = bu.server_user_id where su.server_id = {server_id} ORDER BY bu.count DESC LIMIT 3"
            )