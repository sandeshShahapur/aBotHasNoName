import time
import pytz
from functools import wraps

def convert_utc_to_ist(datetime_utc):
    return datetime_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Kolkata'))

def timer(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()
        ctx = await func(self, *args, **kwargs)
        end_time = time.time()
        await ctx.send(f"{func.__name__} took {(end_time - start_time):.2f} seconds to complete.")
    return wrapper