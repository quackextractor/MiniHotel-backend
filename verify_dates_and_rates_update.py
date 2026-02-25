import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api"
headers = {"Content-Type": "application/json"}

# Use login if the endpoints require a token (assuming auth setup from previous tests)
def get_token():
    print("Logging in to get token...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin"})
    if resp.status_code == 200:
        return resp.json().get('token')
    else:
        print(f"Login failed: {resp.text}")
        return None

def verify_rates():
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        print("Continuing without token, endpoints might fail if protected")

    print("\n--- Testing Seasonal Rates CRUD ---\n")

    # 1. Create a rate
    print("1. Creating a new temporary rate...")
    new_rate = {
        "name": "TEST RATE API UPDATE",
        "start_date": "2026-12-01",
        "end_date": "2026-12-15",
        "rate_multiplier": 2.5
    }
    resp = requests.post(f"{BASE_URL}/seasonal-rates", json=new_rate, headers=headers)
    
    if resp.status_code != 201:
        print(f"Failed to create rate: {resp.status_code} {resp.text}")
        return
    created_rate = resp.json()
    rate_id = created_rate['id']
    print(f"Rate created: {created_rate['name']} (ID: {rate_id})")

    # 2. Read rates (verify it's there)
    print("\n2. Verifying rate in list...")
    resp = requests.get(f"{BASE_URL}/seasonal-rates", headers=headers)
    rates = resp.json()
    found = any(r['id'] == rate_id for r in rates)
    if found:
        print("SUCCESS: Rate found in list!")
    else:
        print("FAILURE: Rate not found in list")

    # 3. Update the rate
    print("\n3. Updating the rate...")
    update_data = {
        "name": "TEST RATE API UPDATED",
        "rate_multiplier": 3.0
    }
    resp = requests.put(f"{BASE_URL}/seasonal-rates/{rate_id}", json=update_data, headers=headers)
    if resp.status_code == 200:
         updated_rate = resp.json()
         if updated_rate['name'] == update_data['name'] and updated_rate['rate_multiplier'] == update_data['rate_multiplier']:
             print("SUCCESS: Rate updated correctly!")
         else:
             print("FAILURE: Rate update logic did not apply changes correctly.")
    else:
         print(f"Failed to update rate: {resp.status_code} {resp.text}")

    # 4. Delete the rate
    print("\n4. Deleting the rate...")
    resp = requests.delete(f"{BASE_URL}/seasonal-rates/{rate_id}", headers=headers)
    if resp.status_code == 200:
         print("SUCCESS: Rate deleted.")
    else:
         print(f"Failed to delete rate: {resp.status_code} {resp.text}")

    # 5. Verify deletion
    print("\n5. Verifying rate deletion...")
    resp = requests.get(f"{BASE_URL}/seasonal-rates", headers=headers)
    rates = resp.json()
    found = any(r['id'] == rate_id for r in rates)
    if not found:
        print("SUCCESS: Rate no longer in list!")
    else:
        print("FAILURE: Rate is still in the list after deletion.")


if __name__ == "__main__":
    verify_rates()
