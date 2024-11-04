from functools import wraps

from flask import g


class Decorators:
    @staticmethod
    def class_roles_required(role):
        def decorator(cls):
            for attr in dir(cls):
                original_method = getattr(cls, attr)
                if callable(original_method) and not attr.startswith("__"):
                    @wraps(original_method)
                    def wrapped_method(*args, **kwargs):
                        # Check if there is a user in the context
                        if g.user and g.user.has_role(role):
                            return original_method(*args, **kwargs)
                        return {"message": "Access denied"}, 403  # Or handle as needed

                    # Replace the method with the wrapped one
                    setattr(cls, attr, wrapped_method)
            return cls
        return decorator