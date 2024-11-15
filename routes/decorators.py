from functools import wraps

from flask import abort
from flask import g
from flask_jwt_extended import jwt_required


def jwt_roles_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if required_role not in g.roles:
                abort(403, message="Access Forbidden for the user")
            return func(*args, **kwargs)
        return wrapper
    return decorator