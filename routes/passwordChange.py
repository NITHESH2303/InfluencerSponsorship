from flask_restful import Resource, reqparse
from flask_security import auth_required, current_user, verify_password
from flask_security.views import change_password

from application.response import create_response


class PasswordChangeAPI(Resource):
    def __init__(self):
        self.auth_input_fields = reqparse.RequestParser()
        self.auth_input_fields.add_argument("old_password", type=str, required=True, help="Enter Your Old Password")
        self.auth_input_fields.add_argument("new_password", type=str, required=True, help="Enter Your New Password")

    @auth_required()
    def post(self):
        args = self.auth_input_fields.parse_args()
        old_password = args["old_password"]
        new_password = args["new_password"]

        if not old_password or not new_password:
            return create_response("Old password and new password are required", 400)

        if not verify_password(old_password, current_user.password):
            return create_response("Invalid old password", 401)

        try:
            change_password(current_user, new_password)
            return create_response("Password changed successfully", 200)
        except Exception as e:
            return create_response(f"Error: {str(e)}", 500)
