import requests


def get_key_access():
    id = 4011
    secret_key = "v3.r.139361338.b537d7f8cc426e40e05e66d2e9d8961dd504351a.4e3767e4fea9205c34c41f95a9fa85ee729ca178"
    headers = {
    "X-Api-App-Id": secret_key
    }
    return headers

