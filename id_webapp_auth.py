# -*- coding: utf-*-
# utilities for web application authentication
import datetime
import jwt

TOKEN_PREFIX: str = 'AT '


def encode_auth_token(secret_key: str, user_id: str) -> str:
    now: datetime.datetime = datetime.datetime.utcnow()
    expiration: datetime.datetime = now + datetime.timedelta(minutes=15)
    payload = {
        'exp': expiration,
        'iat': now,
        'sub': user_id
    }
    return TOKEN_PREFIX + jwt.encode(
        payload,
        secret_key,
        algorithm='HS256'
    )


def decode_auth_token(secret_key: str, auth_token: str) -> str:
    if auth_token is None or len(auth_token) == 0 or not auth_token.startswith(TOKEN_PREFIX):
        # noinspection PyTypeChecker
        return None
    try:
        payload = jwt.decode(auth_token[len(TOKEN_PREFIX):], secret_key, algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        raise ValueError('Authentication expired. Please log in again.')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token. Please log in again.')
