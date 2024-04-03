import discord
from data.databases.users import (
                            set_user, 
                            set_server_user, 
                            get_server_user
                        )
from data.databases.servers import (
                            get_server,
                            set_server
                        )
from data.databases.roles import (
                        get_server_user_roles,
                        delete_server_user_role,
                        set_server_user_role
                    )
from data.databases.plugins import (
                        get_plugin_config_template,
                        get_plugins,
                        get_server_plugin_config,
                        get_subplugin_config_template,
                        get_subplugins,
                        set_server_plugin_config,
                        set_server_subplugin_config,
)
                        
from data.databases.plugins import (
                        get_plugins,
                        get_subplugins,
                        set_server_plugin,
                        get_server_plugin,
                        set_server_subplugin,
                        get_server_subplugin
                    )
from Cogs.Plugins.Invites import (
                                    set_invite
)
import json
from typing import Optional
import time

'''setup | sync

   setup or sync the database for a server for all applicable tables.
   database for a server is made to be in ideal state.
'''
async def update_db(ctx, db_pool, server):
    await ctx.send(f'Setting up {ctx.guild.name}...')
    await ctx.send(f'Loading users and their roles')
    #TODO potential data inconsistency where the bot is removed from the server and a member when removed a role, the bot would not be able to remove the role from the database.
    await set_server(db_pool, server.id)
    users = server.members

    count = 0
    for user in users:
        await set_user(db_pool, user.id)
        await set_server_user(db_pool, server.id, user.id)

        server_user = await get_server_user(db_pool, server.id, user.id)
        if server_user:
            count += await sync_user_roles(db_pool, user)
        else:
            await ctx.send(f'Failed to load {user.name}')
    await ctx.send(f'**{count}** roles synced')

    await set_user(db_pool, -1)
    await set_server_user(db_pool, server.id, -1) #for invaild users
    await ctx.send(f'Users and their roles loaded')

    await ctx.send(f'Loding plugins and their subplugins')
    for plugin in await get_plugins(db_pool):
        await validate_server_plugin(db_pool, server, plugin['name'])

    for subplugin in await get_subplugins(db_pool):
        #TODO validate subplugin
        await set_server_subplugin(db_pool, server.id, subplugin['name'])

        subplugin_config = await get_subplugin_config_template(db_pool, subplugin['name'])
        if subplugin_config:
            server_subplugin = await get_server_subplugin(db_pool, server.id, subplugin['name'])
            subplugin_config = subplugin_config
            if 'server_id' in subplugin_config:
                subplugin_config['server_id'] = server.id
            await set_server_subplugin_config(db_pool, server_subplugin["id"], subplugin_config)
    await ctx.send(f'Plugins and their subplugins loaded')
            
    await ctx.send(f'{server.name} setup complete!')
    return ctx


'''validations

   validate the minimum required data for a functionality to work properly.
   here server data is not synced entirely. database for a server may not be in ideal state.
'''
async def validate_server(db_pool, server):
    if not (await get_server(db_pool, server.id)):
        await update_db(db_pool, server)
        return False
    return True

#TODO optimise this
async def validate_server_plugin(db_pool, server, plugin, validate_server_flag=False):
    if validate_server_flag:
        await validate_server(db_pool, server)

    server_plugin = await get_server_plugin(db_pool, server.id, plugin)
    if not server_plugin:
        await set_server_plugin(db_pool, server.id, plugin)
        server_plugin = await get_server_plugin(db_pool, server.id, plugin)

    plugin_config = await get_plugin_config_template(db_pool, plugin)
    if plugin_config:
        server_plugin_config = await get_server_plugin_config(db_pool, server_plugin['id'])
        if not server_plugin_config:
            if 'server_id' in plugin_config:
                plugin_config['server_id'] = server.id
            await set_server_plugin_config(db_pool, server_plugin['id'], plugin_config)

    return server_plugin

''' conditionally validate server.
    if the user was already in our database, it is likely that is user is synced in our database with the server.
    if the user was not in our database, then the user is not synced in our database with the server.
'''
async def validate_user(db_pool, server, user_id, validate_server_flag=False):
    if validate_server_flag:
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
    server_user = await validate_user(db_pool, server, after.id, validate_server_flag=True)

    if not server_user[0]:
        return print(f'Error: User {after.name} not found in database.')
    
    if not server_user[1]:
        return sync_user_roles(db_pool, after)
        

    before_roles = [role.id for role in before.roles]
    after_roles = [role.id for role in after.roles]
    removed_roles = [role for role in before_roles if role not in after_roles]
    added_roles = [role for role in after_roles if role not in before_roles]

    for role in added_roles:
        await delete_server_user_role(db_pool, server_user[0], role)
    for role in removed_roles:
        await set_server_user_role(db_pool, server_user[0], role)

async def sync_user_roles(db_pool, user: Optional[discord.Member], validate=False):
    if validate:
        server_user = await validate_user(db_pool, user.guild, user.id, validate_server_flag=True)
    else:
        server_user = [await get_server_user(db_pool, user.guild.id, user.id), False]

    if not server_user[0]:
        print(f'Error: User {user.name} not found in database.')
        return 0
    
    cur_roles = [role.id for role in user.roles]
    db_roles = [role['role_id'] for role in await get_server_user_roles(db_pool, server_user[0])]

    count = 0
    for cur_role in cur_roles:
        if cur_role not in db_roles:
            await set_server_user_role(db_pool, server_user[0], cur_role)
            count += 1
    for db_role in db_roles:
        if db_role not in cur_roles:
            await delete_server_user_role(db_pool, server_user[0], db_role)
            count += 1
    return count
        


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