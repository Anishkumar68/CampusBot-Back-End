import requests

BASE_URL = "http://localhost:8000"


# 1️⃣ Register User
def test_register():
    payload = {
        "email": "legendtest123@gmail.com",
        "full_name": "Test User",
        "password": "testpass123",
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print("REGISTER:", response.status_code, response.json())
    return response.status_code


# 2️⃣ Login User (Normal JSON Login)
def test_login():
    payload = {
        "email": "legendtest123@gmail.com",
        "password": "testpass123",
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    print("LOGIN JSON:", response.status_code, response.json())
    tokens = response.json()
    return tokens


# 3️⃣ Login OAuth2 way (form based)
def test_login_oauth2():
    payload = {
        "username": "legendtest123@gmail.com",
        "password": "testpass123",
    }
    response = requests.post(f"{BASE_URL}/auth/token", data=payload)
    print("LOGIN OAUTH2:", response.status_code, response.json())
    tokens = response.json()
    return tokens


# 4️⃣ Refresh Access Token
def test_refresh_token(refresh_token):
    payload = {
        "refresh_token": refresh_token,
    }
    response = requests.post(f"{BASE_URL}/auth/refresh", json=payload)
    print("REFRESH:", response.status_code, response.json())
    tokens = response.json()
    return tokens


# 5️⃣ Test Chat API (Send a message)
def test_chat_api(access_token):
    url = "http://localhost:8000/chat/"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "message": "What programs do you offer?",
        "model": "openai",
        "temperature": 0.7,
    }

    response = requests.post(url, json=payload, headers=headers)

    print("Status Code:", response.status_code)
    try:
        print("Response JSON:", response.json())
    except Exception:
        print("Response Text (not JSON):", response.text)


if __name__ == "__main__":
    print("\n=== TESTING API ===")

    # test_register()  # Only run ONCE if you need
    tokens = test_login()
    # tokens = test_login_oauth2()

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    test_refresh_token(refresh_token)
    test_chat_api(access_token)

    print("\n=== TESTING FINISHED ===\n")
