# @client.event - to register an event
# async await - https://www.reddit.com/r/learnprogramming/comments/tya94m/comment/i3qy6ig/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
import asyncio
import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
import logging, logging.handlers
from typing import List, Optional
from databases.events import get_prefix

import asyncpg

load_dotenv("main.env")
class aBotHasNoName(commands.Bot):
    def __init__(
        self,
        *args,
        initial_extensions: List[str],
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.initial_extensions = initial_extensions


    async def setup_hook(self) -> None:
        await super().setup_hook()
        print(f'{self.user} has logged in!')

        logger = logging.getLogger('discord')
        logger.setLevel(logging.INFO)

        handler = logging.handlers.RotatingFileHandler(
            filename='discord.log',
            encoding='utf-8',
            maxBytes=32 * 1024 * 1024,  # 32 MiB
            backupCount=5,  # Rotate through 5 files
        )
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        
        db_pool = await asyncpg.create_pool(dsn=os.getenv('DATABASE_URL'), min_size=16, max_size=32)
        self.db_pool = db_pool

        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")


        print(f'{self.user} has setupped!')

    async def on_connect(self) -> None:
        print(f'{self.user} has connected to Discord!')

    async def on_ready(self) -> None:
        print(f'{self.user} is ready!')

    async def on_disconnect(self) -> None:
        print(f'{self.user} has disconnected from Discord!')

    async def on_resumed(self) -> None:
        print(f'{self.user} has resumed connection in Discord!')


    async def close(self) -> None:
        await super().close()
        print(f'{self.user} has logged out of and exited Discord!')
        await self.db_pool.close()

        
def main() -> None:
    with open('config.json', 'r') as f:
        config = json.load(f)
        owner_id = config['owner_id']

    intents = discord.Intents.all() #intent basically allows a bot to subscribe to specific buckets of events
    initial_extensions = ['Cogs.Stats', 'Cogs.Messages', 'Cogs.Configs']
    description = '''A bot that has no name'''

    bot = aBotHasNoName(
        initial_extensions=initial_extensions,
        command_prefix=get_prefix,
        intents=intents,
        description=description,
        owner_id=owner_id
    ) 
    bot.run(os.getenv('TOKEN')) #run bot

if __name__ == '__main__':
    main()