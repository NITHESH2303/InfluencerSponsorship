from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from flask_security import verify_password, hash_password

from application import User, db
from application.response import create_response


class PasswordChangeAPI(Resource):
    def __init__(self):
        self.auth_input_fields = reqparse.RequestParser()
        self.auth_input_fields.add_argument("old_password", type=str, required=True, help="Enter Your Old Password")
        self.auth_input_fields.add_argument("new_password", type=str, required=True, help="Enter Your New Password")

    @jwt_required()
    def put(self):
        args = self.auth_input_fields.parse_args()
        old_password = args["old_password"]
        new_password = args["new_password"]

        if not old_password or not new_password:
            return create_response("Old password and new password are required", 400)

        current_user_identity = get_jwt_identity()
        user = User.query.filter_by(fs_uniquifier=current_user_identity).first()

        if not user:
            return create_response("User not found", 404)

        if not verify_password(old_password, user.password_hash):
            return create_response("Invalid old password", 401)

        try:
            user.password_hash = hash_password(new_password)
            db.session.commit()
            return create_response("Password changed successfully", 200)
        except Exception as e:
            db.session.rollback()
            return create_response(f"Error: {str(e)}", 500)
