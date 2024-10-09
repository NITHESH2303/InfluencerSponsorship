from datetime import datetime

from sqlalchemy import event

from application import User


def set_deleted_at(mapper, connection, target):
    if hasattr(target, 'deleted_on'):
        target.deleted_on = datetime.utcnow()
        target.deletion_count += 1
    else:
        if target.deleted_on is not None:
            target.restored_on = datetime.utcnow()


event.listen(User, 'before_update', set_deleted_at)