from flask_restful import reqparse, Resource


class UserAPI(Resource):
    def __init__(self):
        self.user_input_fields = reqparse.RequestParser()
        self.user_input_fields.add_argument("user_name", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("first_name", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("last_name", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("email", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("password", required=True, help="This field cannot be blank.")
