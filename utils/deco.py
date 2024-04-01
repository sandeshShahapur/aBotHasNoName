from functools import wraps

def timer(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()
        ctx = await func(self, *args, **kwargs)
        end_time = time.time()
        await ctx.send(f"{func.__name__} took {(end_time - start_time):.2f} seconds to complete.")
    return wrapper

def str_tolower(func, *args, **kwargs):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        as_ = [a.lower() if isinstance(a, str) else a for a in args]
        kws_ = {k: (v.lower() if isinstance(v, str) else v) for k,v in kwargs.items()}
        return func(*as_, **kws_)
    return wrapper