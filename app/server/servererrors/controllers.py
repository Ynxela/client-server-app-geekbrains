from protocol import make_response

def server_error_controller(request):
    raise Exception('server error message')