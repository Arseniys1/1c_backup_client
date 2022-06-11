
def success_response(data, message=None):
    return {
        "success": True,
        "data": data,
        "message": message,
    }


def error_response(data, message=None):
    return {
        "success": False,
        "data": data,
        "message": message,
    }

