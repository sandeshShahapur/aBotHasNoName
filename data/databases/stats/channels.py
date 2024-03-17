async def get_top_channels(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT channel_id, COUNT(*) as message_count FROM messages_main where server_id = {server_id} GROUP BY channel_id ORDER BY message_count DESC LIMIT 3"
            )
