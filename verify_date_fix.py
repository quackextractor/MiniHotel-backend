import requests

BASE_URL = "http://localhost:5000/api"
session = requests.Session()

# Create a unique test user to bypass auth issues
import time
test_username = f"admin_{int(time.time())}"
auth_data = {'username': test_username, 'password': 'test_password'}

print("Registering new user...", test_username)
reg_resp = session.post(f"{BASE_URL}/auth/register", json=auth_data)
if reg_resp.status_code != 201:
    print("Registration failed:", reg_resp.text)
else:
    print("Registration OK")

login_resp = session.post(f"{BASE_URL}/auth/login", json=auth_data)
if login_resp.status_code == 200:
    token = login_resp.json().get('token')
    session.headers['Authorization'] = f"Bearer {token}"
    print("Login OK")
else:
    print("Login failed:", login_resp.text)
    exit(1)

# Create Guest
guest_data = {
    "first_name": "Test",
    "last_name": "User",
    "email": f"test{int(time.time())}@example.com",
    "phone": "123-456-7890"
}
g_resp = session.post(f"{BASE_URL}/guests", json=guest_data)
guest_id = g_resp.json()['id']

# Create Room
room_data = {
    "room_number": f"TEST{int(time.time())}",
    "room_type": "test_suite",
    "capacity": 2,
    "base_rate": 100.0
}
r_resp = session.post(f"{BASE_URL}/rooms", json=room_data)
room_id = r_resp.json()['id']

# Create Invalid Booking
booking_data = {
    "guest_id": guest_id,
    "room_id": room_id,
    "check_in": "2024-11-15",
    "check_out": "2024-11-10", # Invalid!
    "number_of_guests": 1,
    "status": "confirmed"
}
b_resp = session.post(f"{BASE_URL}/bookings", json=booking_data)
print("Invalid Booking Status:", b_resp.status_code)
print("Invalid Booking Response:", b_resp.text)

if b_resp.status_code == 400 and "Check-out date must be after check-in date" in b_resp.text:
    print("Backend test PASSED!")
    exit(0)
else:
    print("Backend test FAILED!")
    exit(1)
