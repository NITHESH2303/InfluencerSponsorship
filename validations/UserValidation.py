from application.response import validation_error


class UserValidation:

    @staticmethod
    def check_for_existing_user(username, email):
        from application.models import User
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return validation_error("User with this username or email already exists.")
