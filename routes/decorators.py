from functools import wraps

from flask import abort
from flask import g


def jwt_roles_required(*required_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not set(required_roles).intersection(set(g.roles)):
                abort(403, message="Access Forbidden for the user")
            return func(*args, **kwargs)
        return wrapper
    return decorator