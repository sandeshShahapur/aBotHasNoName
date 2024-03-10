import pytz

def convert_utc_to_ist(datetime_utc):
    return datetime_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Kolkata'))