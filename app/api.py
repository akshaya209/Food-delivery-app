def get_status_code(endpoint):
    # Simulates a basic API health check
    endpoints = {
        "/health": 200,
        "/menu": 200,
        "/admin": 403
    }
    return endpoints.get(endpoint, 404)
