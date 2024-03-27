import discord
from data.databases.users import get_user, set_user, set_server_user, get_server_user
from data.databases.servers import get_server, set_server
from data.databases.roles import get_server_user_roles, delete_server_user_role, set_server_user_role, set_role_category, get_server_role_category_id
from data.databases.users import set_invite
from typing import Optional
import time

'''setup | sync

   setup or sync the database for a server for all applicable tables.
   database for a server is made to be in ideal state.
'''
async def update_db(ctx, db_pool, server):
    start_time = time.time()

    await ctx.send(f'Setting up {ctx.guild.name}...')
    await ctx.send(f'Loading users and their roles')
    #TODO potential data inconsistency where the bot is removed from the server and a member when removed a role, the bot would not be able to remove the role from the database.
    await set_server(db_pool, server.id)
    users = server.members
    for user in users:
        await set_user(db_pool, user.id)
        await set_server_user(db_pool, server.id, user.id)

        server_user = await get_server_user(db_pool, server.id, user.id)
        if server_user:
            await sync_user_roles(db_pool, user)
        else:
            await ctx.send(f'Failed to load {user.name}')
    await set_server_user(db_pool, server.id, -1) #for invaild users
    await ctx.send(f'Users and their roles loaded')

    await ctx.send(f'Loading invites')
    for invite in await server.invites():
        if invite.inviter:
            server_user = await validate_user(db_pool, server, invite.inviter.id)
        else:
            server_user = await validate_user(db_pool, server, -1)
        await set_invite(db_pool, invite.code, invite.created_at, server_user[0], invite.uses)

            
    await ctx.send(f'{server.name} setup complete!')

    end_time = time.time()
    await ctx.send(f'Setup took {(end_time - start_time):.2f} seconds to complete...')


'''validations

   validate the minimum required data for a functionality to work properly.
   here server data is not synced entirely. database for a server may not be in ideal state.
'''
async def validate_server(db_pool, server):
    if not (await get_server(db_pool, server.id)):
        await update_db(db_pool, server)
        
async def validate_user(db_pool, server, user_id, validate_server=False):
    if validate_server:
        await validate_server(db_pool, server)

    is_synced = True
    if not (await get_server_user(db_pool, server.id, user_id)):
        is_synced = False
        async with db_pool.acquire() as connection:
            async with connection.transaction():
                await set_user(db_pool, user_id)
                await set_server_user(db_pool, server.id, user_id)
    return [await get_server_user(db_pool, server.id, user_id), is_synced]

async def update_user_roles(db_pool, server, before, after):
    server_user = await validate_user(db_pool, server, after.id, validate_server=True)

    if not server_user[0]:
        print(f'Error: User {after.name} not found in database.')
        return
    if not server_user[1]:
        sync_user_roles(db_pool, after)
        return

    before_roles = [role.id for role in before.roles]
    after_roles = [role.id for role in after.roles]
    removed_roles = [role for role in before_roles if role not in after_roles]
    added_roles = [role for role in after_roles if role not in before_roles]

    for role in added_roles:
        await delete_server_user_role(db_pool, server_user[0], role)
    for role in removed_roles:
        await set_server_user_role(db_pool, server_user[0], role)

async def sync_user_roles(db_pool, user: Optional[discord.Member], validate=False):
    if not validate:
        server_user = await validate_user(db_pool, user.guild, user.id, validate_server=True)
    else:
        server_user = [await get_server_user(db_pool, user.guild.id, user.id), False]

    if not server_user[0]:
        print(f'Error: User {user.name} not found in database.')
        return
    
    roles = [role.id for role in user.roles]
    roles_in_db = [role['role_id'] for role in await get_server_user_roles(db_pool, server_user[0])]

    for role in roles:
        if role not in roles_in_db:
            await set_server_user_role(db_pool, server_user[0], role)
    for role in roles_in_db:
        if role not in roles:
            await delete_server_user_role(db_pool, server_user[0], role)
        


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