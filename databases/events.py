import asyncpg, logging

log = logging.getLogger('discord')

async def log_message(db_pool, message_id, server_id, user_id, channel_id, date, time):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                "INSERT INTO messages_main (message_id, server_id, user_id, channel_id, date, time) VALUES ($1, $2, $3, $4, $5, $6)",
                message_id, server_id, user_id, channel_id, date, time
            )
            #todo add logging to file
            #log.info(f'Logged message {message_id} from user {user_id} in server {server_id} in channel {channel_id} at {time} on {date}')