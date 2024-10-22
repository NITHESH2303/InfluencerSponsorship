from application.models import Role, User
from application.database import db

class PreProcess():

    def prepopulate_roles(self):
        roles = [
            {"name": "admin", "description": "Administrator with full access"},
            {"name": "sponsor", "description": "Sponsor who can create campaigns"},
            {"name": "influencer", "description": "Influencer who can accept ad requests"}
        ]
        existing_roles = {role.name for role in Role.query.all()}
        for role in roles:
            if role["name"] not in existing_roles:
                new_role = Role(
                    name=role["name"],
                    description=role["description"],
                )
                db.session.add(new_role)
        db.session.commit()

    def create_admin(self):
        admin_role = Role.query.filter_by(name="admin").one_or_none()
        if not admin_role:
            raise ValueError("Admin role not found. Make sure roles are prepopulated.")

        admin = User.query.filter_by(username="admin").one_or_none()
        if not admin:
            admin = User(
                username='admin',
                first_name='Admin',
                email='nithesh@optigon.in',
            )
            admin.set_password('admin')
            admin.roles.append(admin_role)

            db.session.add(admin)

    def __init__(self):
        try:
            self.prepopulate_roles()
            self.create_admin()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(e)