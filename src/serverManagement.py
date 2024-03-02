"""
targets is a list of discord role/member objects.
amends is a dictionary of permissions to be amended.
syncChannels is a boolean to sync channels with their category.
targets example = [discord.utils.get(guild.roles, id=)]
"""
async def amendPermsAllCategories(guild, targets, amends, syncChannels):
    if guild:
        for category in guild.categories: # Edit permissions for targets in the category
            for target in targets:
                await category.set_permissions(target, **amends)

        # Optionally sync channels with their category
        if syncChannels:
            for channel in category.channels:
                await channel.edit(sync_permissions=True)
        print('Permissions amended.')
    else:
        print('Guild not found.')