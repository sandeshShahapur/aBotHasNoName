# @client.event - to register an event
# async await - https://www.reddit.com/r/learnprogramming/comments/tya94m/comment/i3qy6ig/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button
import discord
import os
import json
from dotenv import load_dotenv
from messages.message_handler import process_messages


with open("aBotHasNoName\config.json", "r") as json_file:
    config = json.load(json_file)

intents = discord.Intents().all() #permissions we are allowing for our bot to access (intents determine which events discord will send to your app)
client = discord.Client(intents=intents) #our bot, the connection to discord

prefix = config["prefix"]
guildId = 950272762340061185 #936102218434769008

# event that is run when our bot is online and ready to start being used
@client.event
async def on_ready(): 
    print('We have logged in as {0.user}'.format(client))
    guild = client.get_guild(guildId)

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return
    
    await process_messages(message, prefix)

load_dotenv()
token = os.getenv('TOKEN')
if token is None:
    print("TOKEN environment variable not set. Using default token.")
    token = "MTIxMDU3MzA0ODE2ODcxNDI5MA.GROhsj.RgzzCtN9o7gBO3Zi9tegIXraCu1_gMvaU1wVAQ"
client.run(token) #running the bot by supplying our token which is like the password for our bot