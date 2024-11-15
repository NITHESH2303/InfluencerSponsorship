from flask import jsonify, make_response


def create_response(message, status_code, data=None):
    response = {
        'status': 'success' if status_code < 400 else 'error',
        'message': message
    }
    if data:
        response['data'] = data
    return make_response(jsonify(response), status_code)


# Success Messages
def success(data=None):
    return create_response("Request was successful", 200, data)


def created(data=None):
    return create_response("Resource created successfully", 201, data)


# Error Messages
def user_not_found(resource_name, inp_type):
    return create_response(f"No {inp_type} with {resource_name} found", 404)


def file_not_found():
    return create_response("Requested file not found", 404)

def resource_not_found():
    return create_response("User not found", 404)


def validation_error(message):
    return create_response(f"Validation error: {message}", 400)


def duplicate_entry(resource_name, error):
    return create_response(f"Duplicate entry for {resource_name} with Exception : {error}", 409)


def unauthorized():
    return create_response("Unauthorized access", 401)


def forbidden():
    return create_response("Access forbidden", 403)


def internal_server_error(exception):
    return create_response(f"An internal server error occurred : {exception}", 500)
