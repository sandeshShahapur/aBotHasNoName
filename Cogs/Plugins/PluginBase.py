from data.databases.core.db_management import validate_server_plugin
from data.databases.Plugins.plugins import (
                                    get_server_plugin_config,
                                    get_server_plugin_enabled,
                                    set_server_plugin_config,
                                    set_server_plugin_enabled
                                )
import json


async def plugin_enable(self, ctx, plugin, module):
    server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, plugin, validate_server_flag=True)
    if not server_plugin:
        self.bot.logger.error(f'Error: Plugin bumper for Server {ctx.guild.name} ({ctx.guild.id}) not found in database.') # noqa
        return await ctx.send('bumper plugin not found in database.')

    if not module:
        if await get_server_plugin_enabled(ctx.bot.db_pool, server_plugin['id']):
            await ctx.send(f'{plugin} is already enabled in this server.')
        else:
            await set_server_plugin_enabled(ctx.bot.db_pool, server_plugin['id'], True)
            await ctx.send(f'{plugin} has been enabled in this server.')
        return

    if module not in self.modules:
        return await ctx.send(f'{module} is not a valid module.')

    server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
    if server_config[module]["enabled"]:
        await ctx.send(f'{module} is already enabled.')
    else:
        server_config[module]["enabled"] = True
        await set_server_plugin_config(self.bot.db_pool, server_plugin['id'], server_config)
        await ctx.send(f'{module} has been enabled.')


async def plugin_disable(self, ctx, plugin, module):
    server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, plugin, validate_server_flag=True)
    if not server_plugin:
        self.bot.logger.error(f'Error: Plugin bumper for Server {ctx.guild.name} ({ctx.guild.id}) not found in database.') # noqa
        return await ctx.send(f'{plugin} plugin not found in database.')

    if not module:
        if not await get_server_plugin_enabled(self.bot.db_pool, ctx.guild.id, plugin):
            return await ctx.send(f'{plugin} is already disabled in this server.')
        else:
            await set_server_plugin_enabled(self.bot.db_pool, server_plugin['id'], False)
            await ctx.send(f'{plugin} has been disabled in this server.')
        return

    if module not in self.modules:
        return await ctx.send(f'{module} is not a valid module.')

    server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
    if not server_config[module]["enabled"]:
        await ctx.send(f'{module} is already disabled.')
    else:
        server_config[module]["enabled"] = False
        await set_server_plugin_config(self.bot.db_pool, server_plugin['id'], server_config)
        await ctx.send(f'{module} has been disabled.')


async def view_config(self, ctx, plugin, module):
    server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, plugin, validate_server_flag=True)
    if not server_plugin:
        return await ctx.send(f'{plugin} plugin not found in database.')

    server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
    if not module:
        await ctx.send(f' ```json\n{json.dumps(server_config, indent=4)}\n``` ')
    else:
        if module not in self.modules:
            return await ctx.send(f"{module} is not a valid module.")
        await ctx.send(f' ```json\n{json.dumps(server_config[module], indent=4)}\n``` ')


async def set_config(self, ctx, plugin, module, **kwargs):
    server_plugin = await validate_server_plugin(self.bot.db_pool, ctx.guild, plugin, validate_server_flag=True)
    if not server_plugin:
        return self.bot.logger.error(f'Error: Plugin bumper for Server {ctx.guild.name} ({ctx.guild.id}) not found in database.') # noqa

    server_config = await get_server_plugin_config(self.bot.db_pool, server_plugin['id'])
    for key, value in kwargs.items():
        if module:
            server_config[module][key] = value
        else:
            server_config[key] = value
    await set_server_plugin_config(self.bot.db_pool, server_plugin['id'], server_config)
    await ctx.send('Configuration has been set.')
