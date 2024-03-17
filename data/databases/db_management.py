import discord
from data.databases.stats.users import get_user, set_user, set_server_user, get_server_user
from data.databases.stats.servers import get_server, set_server
from data.databases.stats.roles import get_server_user_roles, delete_server_user_role, set_server_user_role, set_role_category, get_server_role_category_id
import time

# *update and validata data in db

async def update_db(ctx, db_pool, server):
    start_time = time.time()

    await ctx.send(f'Setting up {ctx.guild.name}...')

    # .loading all the present users and their roles in the server to the database.
    await ctx.send(f'Loading users and their roles in {server.name}...')
    await ctx.send(f'Loading users and their roles in {server.name}...')
    #TODO potential data inconsistency where the bot is removed from the server and a member when removed a role, the bot would not be able to remove the role from the database.
    await set_server(db_pool, server.id)
    users = server.members
    for user in users:
        await set_user(db_pool, user.id)
        await set_server_user(db_pool, server.id, user.id)

        server_user = await get_server_user(db_pool, server.id, user.id)
        if server_user:
            roles = user.roles
            for role in roles:
                await set_server_user_role(db_pool, server_user, role.id)
    await ctx.send(f'{server.name} setup complete!')

    end_time = time.time()
    await ctx.send(f'Setup took {end_time - start_time} seconds to complete...')

async def validate_server(db_pool, server):
    server = await get_server(db_pool, server.id)
    if not server:
        await update_db(db_pool, server.id)
        
async def validate_user(db_pool, server, user_id):
    await validate_server(db_pool, server)

    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await set_user(db_pool, user_id)
            await set_server_user(db_pool, server.id, user_id)
            return await get_server_user(db_pool, server.id, user_id)

async def update_user_roles(db_pool, user: discord.Member):
    server_user = await validate_user(db_pool, user.guild, user.id)

    roles = [role.id for role in user.roles]
    roles_in_db = [role['role_id'] for role in await get_server_user_roles(db_pool, server_user)]

    for role in roles:
        if role not in roles_in_db:
            await set_server_user_role(db_pool, server_user, role)
    for role in roles_in_db:
        if role not in roles:
            await delete_server_user_role(db_pool, server_user, role)
        


async def flush_db(db_pool, table, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"DELETE FROM {table} WHERE server_id = {server_id}"
            )
            
async def flush_db_all(db_pool, table, server_id):
    async with db_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                f"DELETE FROM {table} WHERE server_id = {server_id}"
            )