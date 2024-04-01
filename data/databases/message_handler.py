async def log_message(db_pool, message_id, server_id, user_id, channel_id, sent_at):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO messages (message_id, server_id, user_id, channel_id, sent_at) VALUES ($1, $2, $3, $4, $5) ON CONFLICT (message_id) DO NOTHING",
                message_id, server_id, user_id, channel_id, sent_at
            )
            #todo add logging to file
            #log.info(f'Logged message {message_id} from user {user_id} in server {server_id} in channel {channel_id} at {time} on {date}')