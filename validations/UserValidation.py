class UserValidation:
    @staticmethod
    def validate_role_assignment(current_roles, new_role):
        if 'Admin' in current_roles and new_role in ['Influencer', 'Sponsor']:
            raise ValueError("Admin users cannot also be Influencers or Sponsors")

        if new_role == 'Admin' and any(role in current_roles for role in ['Influencer', 'Sponsor']):
            raise ValueError("Influencers or Sponsors cannot also be Admins")