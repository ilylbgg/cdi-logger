import hashlib
from datetime import datetime

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def round_hour(dt=None):
    if dt is None:
        dt = datetime.now()
    return dt.replace(minute=0, second=0, microsecond=0)

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

# ...other utility functions...
