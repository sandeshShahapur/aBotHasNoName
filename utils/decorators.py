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

def tolower(func, *args, **kwargs):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        as_ = [a.lower() if isinstance(a, str) else a for a in args]
        kws_ = {k: (v.lower() if isinstance(v, str) else v) for k,v in kwargs.items()}
        return await func(*as_, **kws_)
    return wrapper