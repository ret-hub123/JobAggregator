import requests


def get_key_access():
    id = 4011
    secret_key = "v3.r.139361338.b537d7f8cc426e40e05e66d2e9d8961dd504351a.4e3767e4fea9205c34c41f95a9fa85ee729ca178"
    headers = {
    "X-Api-App-Id": secret_key
    }
    return headers


def test_superjob_key(api_key):

    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {
        'X-Api-App-Id': api_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {'count': 1}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ Ключ работает!")
            return True
        else:
            print("❌ Ключ не работает")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

test_superjob_key("v3.r.139361338.b537d7f8cc426e40e05e66d2e9d8961dd504351a.4e3767e4fea9205c34c41f95a9fa85ee729ca178")

