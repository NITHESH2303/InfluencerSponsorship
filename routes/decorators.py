from flask_security import roles_required



def class_roles_required(role):
    def decorator(cls):
        for attr in dir(cls):
            if callable(getattr(cls, attr)) and not attr.startswith("__"):
                method = getattr(cls, attr)
                setattr(cls, attr, roles_required(role)(method))
        return cls
    return decorator
