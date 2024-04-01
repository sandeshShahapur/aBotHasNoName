'''''''''''''''''''''''''PLUIGN MANAGEMENT'''''''''''''''''''''''''''
async def get_plugins(db_pool):
    async with db_pool.acquire() as connection:
        return await connection.fetch('SELECT name FROM plugins')
    
async def get_subplugins(db_pool):
    async with db_pool.acquire() as connection:
        return await connection.fetch('SELECT name FROM subplugins')
    
async def get_plugin_config_template(db_pool, plugin_name):
    async with db_pool.acquire() as connection:
        return await connection.fetchval('SELECT config_template FROM plugin_config_templates WHERE plugin_name = $1', plugin_name)

async def get_subplugin_config_template(db_pool, subplugin_name):
    async with db_pool.acquire() as connection:
        return await connection.fetchval('SELECT config_template FROM subplugin_config_templates WHERE subplugin_name = $1', subplugin_name)    


async def set_server_plugin(db_pool, server_id, plugin_name):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_plugins (server_id, plugin_name) VALUES ($1, $2) ON CONFLICT (server_id, plugin_name) DO NOTHING',
                server_id, plugin_name
            )

async def get_server_plugin(db_pool, server_id, plugin_name):
    async with db_pool.acquire() as connection:
        return await connection.fetchrow('SELECT * FROM server_plugins WHERE server_id = $1 AND plugin_name = $2', server_id, plugin_name)
    
async def set_server_plugin_config(db_pool, server_plugin_id, config):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_plugin_configs (server_plugin_id, config) VALUES ($1, $2) ON CONFLICT (server_plugin_id) DO UPDATE SET config = $2',
                server_plugin_id, config
            )

async def get_server_plugin_config(db_pool, server_plugin_id):
    async with db_pool.acquire() as connection:
        return await connection.fetchval('SELECT config FROM server_plugin_configs WHERE server_plugin_id = $1', server_plugin_id)

    
async def get_server_subplugin(db_pool, server_id, subplugin_name):
    async with db_pool.acquire() as connection:
        return await connection.fetchrow('SELECT * FROM server_subplugins WHERE server_id = $1 AND subplugin_name = $2', server_id, subplugin_name)

async def set_server_subplugin(db_pool, server_id, subplugin_name):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_subplugins (server_id, subplugin_name) VALUES ($1, $2) ON CONFLICT (server_id, subplugin_name) DO NOTHING',
                server_id, subplugin_name
            )

async def set_server_subplugin_config(db_pool, server_subplugin_id, config):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_subplugin_configs (server_subplugin_id, config) VALUES ($1, $2) ON CONFLICT (server_subplugin_id) DO UPDATE SET config = $2',
                server_subplugin_id, config
            )

async def get_server_subplugin_config(db_pool, server_subplugin_id):
    async with db_pool.acquire() as connection:
        return await connection.fetchval('SELECT config FROM server_subplugin_configs WHERE server_subplugin_id = $1', server_subplugin_id)


async def set_server_plugin_enabled(db_pool, server_plugin_id, enabled):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'UPDATE server_plugins SET enabled = $1 WHERE id = $2',
                enabled, server_plugin_id
            )

async def get_server_plugin_enabled(db_pool, server_plugin_id):
    async with db_pool.acquire() as connection:
        return await connection.fetchval('SELECT enabled FROM server_plugins WHERE id = $1', server_plugin_id)

async def get_server_plugin_config(db_pool, server_plugin_id):
    async with db_pool.acquire() as connection:
        return await connection.fetchrow('SELECT config FROM server_plugin_configs WHERE server_plugin_id = $1', server_plugin_id)
    

async def set_server_plugin_config(db_pool, server_plugin_id, config):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_plugin_configs (server_plugin_id, config) VALUES ($1, $2) ON CONFLICT (server_plugin_id) DO UPDATE SET config = $2',
                server_plugin_id, config
            )

async def get_server_plugin_config(db_pool, server_plugin_id):
    async with db_pool.acquire() as connection:
        return await connection.fetchval('SELECT config FROM server_plugin_configs WHERE server_plugin_id = $1', server_plugin_id)
    

'''''''''''''''''''''''''''BUMPER PLUGIN'''''''''''''''''''''''''''''
async def bump(db_pool, server_id, user_id, channel_id, bumped_at, should_remind, should_miss_remind):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO bumps (server_id, user_id, channel_id, bumped_at) VALUES ($1, $2, $3, $4, $5, $6) on CONFLICT DO NOTHING',
                server_id, user_id, channel_id, bumped_at, should_remind, should_miss_remind
            )

async def get_bump(db_pool, server_id):
    async with db_pool.acquire() as connection:
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
        return await connection.fetchval(
            f"SELECT SUM(count) FROM bump_counts bc INNER JOIN server_users su ON bc.server_user_id = su.id where su.server_id = $1 GROUP BY server_id",
            server_id
        )
    
async def get_server_user_bump_count(db_pool, server_user_id):
    async with db_pool.acquire() as connection:
        return await connection.fetchval(
            f"SELECT count FROM bump_counts WHERE server_user_id = $1",
            server_user_id
        )