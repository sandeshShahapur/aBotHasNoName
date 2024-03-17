async def log_message(db_pool, message_id, server_id, user_id, channel_id, date, time):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO messages_main (message_id, server_id, user_id, channel_id, date, time) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (message_id) DO NOTHING",
                message_id, server_id, user_id, channel_id, date, time
            )
            #todo add logging to file
            #log.info(f'Logged message {message_id} from user {user_id} in server {server_id} in channel {channel_id} at {time} on {date}')

async def bump(db_pool, server_user):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            count = await connection.fetchval(
                f"SELECT counts FROM bumps WHERE server_user_id = {server_user}"
            )
            if not count:
                count = 1
            else:
                count += 1
            
            await connection.execute(
                f"INSERT INTO bumps (server_user_id, counts) VALUES ($1, $2) ON CONFLICT (server_user_id) DO UPDATE SET counts = $2",
                server_user, count
            )

            return count