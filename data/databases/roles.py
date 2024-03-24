'''''''''''''''''''''SERVER USER'''''''''''''''''''''''
async def get_server_user_roles(db_pool, server_user_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT role_id FROM server_user_roles where server_user_id = {server_user_id}"
            )

async def set_server_user_role(db_pool, server_user_id, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO server_user_roles (server_user_id, role_id) VALUES ($1, $2) ON CONFLICT (server_user_id, role_id) DO NOTHING",
                server_user_id, role_id
            )

async def delete_server_user_role(db_pool, server_user_id, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"DELETE FROM server_user_roles WHERE server_user_id = {server_user_id} AND role_id = {role_id}"
            )

#TODO update        
async def delete_role(db_pool, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"DELETE FROM server_user_roles WHERE role_id = {role_id}"
            )


'''''''''''''''''''''ROLE CATEGORY'''''''''''''''''''''''
async def set_role_category(db_pool, role_category):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO role_categories (name) VALUES ($1) ON CONFLICT (name) DO NOTHING",
                role_category
            )

async def get_server_role_category_id(db_pool, server_id, role_category):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                f"SELECT id FROM server_role_categories WHERE server_id = {server_id} AND role_category_name = '{role_category}'"
            )

async def set_server_role_category_id(db_pool, server_id, category):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO server_role_categories (server_id, role_category_name) VALUES ($1, $2) ON CONFLICT (server_id, role_category_name) DO NOTHING",
                server_id, category
            )

async def get_server_role_categories(db_pool, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT role_category_name FROM server_role_categories WHERE server_id = {server_id}"
            )
        
async def get_roles_in_category(db_pool, category_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT role_id FROM server_role_categories_roles WHERE server_role_category_id = {category_id}"
            )
        
async def delete_server_role_category_roles(db_pool, server_role_category_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"DELETE FROM server_role_categories_roles WHERE server_role_category_id = {server_role_category_id}"
            )

async def delete_server_role_category_id(db_pool, server_role_category_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"DELETE FROM server_role_categories WHERE id = {server_role_category_id}"
            )
    
async def delete_role_category(db_pool, role_category):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            category_exists_for_other_servers = await category_exists(db_pool, role_category)
            if not category_exists_for_other_servers:
                await connection.execute(
                    f"DELETE FROM role_categories WHERE name = '{role_category}'"
                )

async def category_exists(db_pool, role_category):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT role_category_name FROM server_role_categories WHERE role_category_name = '{role_category}'"
            )
        
async def set_server_role_category_role(db_pool, server_role_category_id, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"INSERT INTO server_role_categories_roles (server_role_category_id, role_id) VALUES ($1, $2) ON CONFLICT (server_role_category_id, role_id) DO NOTHING",
                server_role_category_id, role_id
            )

async def delete_server_role_category_role(db_pool, server_role_category_id, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"DELETE FROM server_role_categories_roles WHERE server_role_category_id = {server_role_category_id} AND role_id = {role_id}"
            )


'''''''''''''''''''''ROLE STATS'''''''''''''''''''''''
async def get_role_count(db_pool, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetchval(
                f"SELECT COUNT(*) from server_user_roles where role_id = {role_id}"
            )
        
async def get_categories_of_role(db_pool, role_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            return await connection.fetch(
                f"SELECT role_category_name from server_role_categories where id in (SELECT server_role_category_id from server_role_categories_roles where role_id = {role_id})"
            )