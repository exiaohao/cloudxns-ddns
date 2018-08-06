

def json_success(data, status_code=200, message="success"):
    return {
        "status_code": status_code,
        "data": data,
        "message": message,
    }

def json_error(error_message="Error occured", status_code=400):
    return {
        "status_code": status_code,
        "data": None,
        "message": error_message,
    }
