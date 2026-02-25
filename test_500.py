import requests
import time

BASE_URL = "http://localhost:5000/api"

# Login
auth_data = {'username': 'admin', 'password': 'admin'}
reg_resp = requests.post(f"{BASE_URL}/auth/register", json=auth_data)
login_resp = requests.post(f"{BASE_URL}/auth/login", json=auth_data)
if login_resp.status_code == 200:
    token = login_resp.json().get('token')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Try sending bad payload
    payload = {
        "room_number": f"TEST{int(time.time())}",
        "room_type": "standard",
        "capacity": 2,
        "base_rate": 100.0,
        "group_id": None,
        "amenities": ""
    }
    resp = requests.post(f"{BASE_URL}/rooms", json=payload, headers=headers)
    print("STATUS:", resp.status_code)
    try:
        print("JSON:", resp.json())
    except:
        print("TEXT:", resp.text)
else:
    print("Failed to login", login_resp.text)
