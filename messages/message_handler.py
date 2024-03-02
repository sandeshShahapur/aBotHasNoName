from datetime import datetime, timedelta
import pytz

from .commands import process_command
from .chats import process_chat
from databases.messages.messages_main import log_message

def convert_utc_to_ist(utc_time):
    return utc_time.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Kolkata'))

async def process_messages(message, prefix):
    m_id = message.id
    server = message.guild.id
    user = message.author.id
    channel = message.channel.id
    date_time = convert_utc_to_ist(message.created_at)
    date = date_time.date()
    time = date_time.time()
    await log_message(m_id, server, user, channel, date, time)

    if message.content.startswith(prefix):
        await process_command(message, prefix)
    else:
        await process_chat(message) #await process_chat(message)