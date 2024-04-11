'''''''''''''''''''''''''''BUMPER PLUGIN'''''''''''''''''''''''''''''
async def bump(db_pool, server_id, user_id, channel_id, bumped_at, should_remind, should_miss_remind):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO bumps (server_id, user_id, channel_id, bumped_at, should_remind, should_miss_remind) VALUES ($1, $2, $3, $4, $5, $6)'
                + ' ON CONFLICT (server_id) DO UPDATE SET user_id = $2, channel_id = $3, bumped_at = $4, should_remind = $5, should_miss_remind = $6',
                server_id, user_id, channel_id, bumped_at, should_remind, should_miss_remind
            )

async def get_bump(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow('SELECT * FROM bumps WHERE server_id = $1', server_id)
    
async def update_bump_reminder(db_pool, server_id, should_remind):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'UPDATE bumps SET should_remind = $1 WHERE server_id = $2',
                should_remind, server_id
            )

async def update_missed_reminder(db_pool, server_id, should_miss_remind):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'UPDATE bumps SET should_miss_remind = $1 WHERE server_id = $2',
                should_miss_remind, server_id
            )

async def bump_counts(db_pool, server_user):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            count = await connection.fetchval(
                f"SELECT count FROM bump_counts WHERE server_user_id = $1",
                server_user
            )
            if not count:
                count = 1
            else:
                count += 1
            
            await connection.execute(
                f"INSERT INTO bump_counts (server_user_id, count) VALUES ($1, $2) ON CONFLICT (server_user_id) DO UPDATE SET count = $2",
                server_user, count
            )

            return count
        
async def get_server_bump_count(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                f"SELECT SUM(count) FROM bump_counts bc INNER JOIN server_users su ON bc.server_user_id = su.id where su.server_id = $1 GROUP BY server_id",
                server_id
            )
    
async def get_server_user_bump_count(db_pool, server_user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                f"SELECT count FROM bump_counts WHERE server_user_id = $1",
                server_user_id
            )