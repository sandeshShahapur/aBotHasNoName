import time
import pytz
from functools import wraps

def convert_utc_to_ist(datetime_utc):
    return datetime_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Kolkata'))

def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken for {func.__name__}: {end_time - start_time}")
    return func