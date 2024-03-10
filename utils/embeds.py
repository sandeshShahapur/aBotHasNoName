import discord
import asyncio

async def create_embed(
    title: str,
    description: str,
    /,
    type: str = 'rich',
    color: discord.Color = discord.Color.blurple(),
    url: str = None,
    footer: str = None,
    footer_icon_url: str = None,
    image_url: str = None,
    thumbnail_url: str = None,
    author_name: str = None,
    author_url: str = None,
    author_icon_url: str = None,
    fields: list = None,
    timestamp: bool = False
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        type=type,
        color=color,
        url=url
    )

    if footer:
        embed.set_footer(text=footer, icon_url=footer_icon_url)
    if image_url:
        embed.set_image(url=image_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if author_name:
        embed.set_author(name=author_name, url=author_url, icon_url=author_icon_url)
    if fields:
        for field in fields:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
    if timestamp:
        embed.timestamp = discord.utils.utcnow()

    return embed