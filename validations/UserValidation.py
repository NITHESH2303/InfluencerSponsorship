from application.response import validation_error


class UserValidation:
    @staticmethod
    def validate_role_assignment(current_roles, new_role):
        if 'Admin' in current_roles and new_role in ['Influencer', 'Sponsor']:
            raise ValueError("Admin users cannot also be Influencers or Sponsors")

        if new_role == 'Admin' and any(role in current_roles for role in ['Influencer', 'Sponsor']):
            raise ValueError("Influencers or Sponsors cannot also be Admins")

    @staticmethod
    def check_for_existing_user(username, email):
        from application.models import User
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return validation_error("User with this username or email already exists.")
