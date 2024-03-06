# @client.event - to register an event
# async await - https://www.reddit.com/r/learnprogramming/comments/tya94m/comment/i3qy6ig/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
import logging


with open("config.json", "r") as json_file:
    config = json.load(json_file)

description = '''A bot that has no name'''
intents = discord.Intents().all() #intent basically allows a bot to subscribe to specific buckets of events
bot = commands.Bot(prefix='.', description=description, intents=intents) #our bot, the connection to discord (Client is a class, while client is an instance of that class)

# event that is run when our bot is online and ready to start being used
@bot.event
async def on_ready(): 
    print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

load_dotenv()
token = os.getenv('TOKEN')
if token is None:
    print("TOKEN environment variable not set. Exiting...")
else:
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    bot.run(token, log_handler=handler, log_level=logging.DEBUG) #running the bot by supplying our token which is like the password for our bot