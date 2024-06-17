import jwt
import time
from config import JWT_SECRET_KEY, JWT_ALGORITHM

def generate_token(user_id, is_admin):
    current_time = time.time()
    exp_time = current_time + 3 * 60 * 60  # Token valid for 3 hours
    payload = {
        'user_id': user_id,
        'is_admin': is_admin,
        'exp': exp_time
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

def verify_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload['user_id'], payload['is_admin']
    except jwt.ExpiredSignatureError:
        return None, None
    except jwt.InvalidTokenError:
        return None, None
