'''''''''''''''''''''''''PLUIGN MANAGEMENT'''''''''''''''''''''''''''


async def get_plugins(db_pool):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT name FROM plugins')


async def get_subplugins(db_pool):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch('SELECT name FROM subplugins')


async def get_plugin_config_template(db_pool, plugin_name):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                'SELECT config_template FROM plugin_config_templates '
                'WHERE plugin_name = $1',
                plugin_name)


async def get_subplugin_config_template(db_pool, subplugin_name):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                'SELECT config_template FROM subplugin_config_templates '
                'WHERE subplugin_name = $1',
                subplugin_name
            )


async def set_server_plugin(db_pool, server_id, plugin_name):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_plugins (server_id, plugin_name) '
                'VALUES ($1, $2) '
                'ON CONFLICT (server_id, plugin_name) DO NOTHING',
                server_id, plugin_name
            )


async def get_server_plugin(db_pool, server_id, plugin_name):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow(
                'SELECT * FROM server_plugins '
                'WHERE server_id = $1 AND plugin_name = $2',
                server_id, plugin_name
            )


async def set_server_plugin_config(db_pool, server_plugin_id, config):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_plugin_configs (server_plugin_id, config) '
                'VALUES ($1, $2) '
                'ON CONFLICT (server_plugin_id) DO UPDATE SET config = $2',
                server_plugin_id, config
            )


async def get_server_plugin_config(db_pool, server_plugin_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                'SELECT config FROM server_plugin_configs '
                'WHERE server_plugin_id = $1',
                server_plugin_id
            )


async def get_server_subplugin(db_pool, server_id, subplugin_name):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchrow(
                'SELECT * FROM server_subplugins '
                'WHERE server_id = $1 AND subplugin_name = $2',
                server_id, subplugin_name
            )


async def set_server_subplugin(db_pool, server_id, subplugin_name):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_subplugins (server_id, subplugin_name) '
                'VALUES ($1, $2) '
                'ON CONFLICT (server_id, subplugin_name) DO NOTHING',
                server_id, subplugin_name
            )


async def set_server_subplugin_config(db_pool, server_subplugin_id, config):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'INSERT INTO server_subplugin_configs (server_subplugin_id, config) '
                'VALUES ($1, $2) '
                'ON CONFLICT (server_subplugin_id) '
                'DO UPDATE SET config = $2',
                server_subplugin_id, config
            )


async def get_server_subplugin_config(db_pool, server_subplugin_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                'SELECT config FROM server_subplugin_configs '
                'WHERE server_subplugin_id = $1',
                server_subplugin_id
            )


async def set_server_plugin_enabled(db_pool, server_plugin_id, enabled):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                'UPDATE server_plugins SET enabled = $1 WHERE id = $2',
                enabled, server_plugin_id
            )


async def get_server_plugin_enabled(db_pool, server_plugin_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                'SELECT enabled FROM server_plugins '
                'WHERE id = $1',
                server_plugin_id
            )
