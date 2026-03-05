import time
import unittest
from datetime import date, timedelta

import requests

# API base URL - adjust as needed
BASE_URL = "http://localhost:5000/api"


class TestMiniHotelAPI(unittest.TestCase):
    """Comprehensive test suite for MiniHotel API"""

    def setUp(self):
        """Set up test data before each test"""
        self.session = requests.Session()
        
        # Authentication - Use consistent admin credentials
        auth_data = {'username': 'admin', 'password': 'admin'}
        
        # Try login first
        login_resp = self.session.post(f"{BASE_URL}/auth/login", json=auth_data)
        
        if login_resp.status_code != 200:
            # Try to register if login failed (maybe first run or clean DB)
            reg_resp = self.session.post(f"{BASE_URL}/auth/register", json=auth_data)
            
            if reg_resp.status_code == 201:
                # Registration successful, login again
                login_resp = self.session.post(f"{BASE_URL}/auth/login", json=auth_data)
            else:
                 print(f"WARNING: Login and Registration failed for admin. DB might require reset. {reg_resp.text}")

        if login_resp.status_code == 200:
            token = login_resp.json().get('token')
            self.session.headers['Authorization'] = f"Bearer {token}"
        else:
            print("WARNING: Authentication failed for tests. Some tests may fail.")

        self.test_guest_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test{int(time.time())}@example.com",
            "phone": f"123-456-{int(time.time() % 10000):04d}",
            "address": "123 Test St"
        }
        self.test_room_data = {
            "room_number": f"TEST{int(time.time())}",
            "room_type": "test_suite",
            "description": "Test room for automated testing",
            "capacity": 2,
            "base_rate": 100.0
        }
        self.test_booking_data = {
            "check_in": (date.today() + timedelta(days=1)).isoformat(),
            "check_out": (date.today() + timedelta(days=3)).isoformat(),
            "number_of_guests": 2,
            "total_amount": 200.0,
            "status": "confirmed"
        }

        # Clean up any existing test data
        self.cleanup_test_data()

    def tearDown(self):
        """Clean up test data after each test"""
        self.cleanup_test_data()

    def cleanup_test_data(self):
        """Clean up test data to avoid conflicts"""
        # This would be more comprehensive in a real test environment
        # For now, we'll rely on the tests to clean up after themselves
        pass

    # Health Check Tests
    def test_health_check(self):
        """Test API health check endpoint"""
        # GET /api/health
        response = self.session.get(f"{BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)

    # Room Tests
    def test_get_rooms(self):
        """Test getting all rooms"""
        # GET /api/rooms
        response = self.session.get(f"{BASE_URL}/rooms")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_create_and_get_room(self):
        """Test creating a room and then retrieving it"""
        # Use unique room number to avoid conflicts
        room_data = self.test_room_data.copy()
        room_data["room_number"] = f"CREATE{int(time.time())}"

        # POST /api/rooms
        response = self.session.post(
            f"{BASE_URL}/rooms",
            json=room_data,
            headers={"Content-Type": "application/json"}
        )
        # Debug: Print response for troubleshooting
        if response.status_code != 201:
            print(f"Room creation failed: {response.status_code} - {response.text}")

        self.assertEqual(response.status_code, 201)
        room_data = response.json()
        self.assertIn("id", room_data)

        # GET /api/rooms/{room_id}
        room_id = room_data["id"]
        response = self.session.get(f"{BASE_URL}/rooms/{room_id}")
        self.assertEqual(response.status_code, 200)
        retrieved_room = response.json()
        self.assertEqual(retrieved_room["room_number"], room_data["room_number"])

        # Store room ID for cleanup
        self.test_room_id = room_id

    def test_create_duplicate_room(self):
        """Test creating a room with duplicate room number"""
        # Use unique room number for first creation
        unique_room_number = f"DUPLICATE{int(time.time())}"
        room_data = self.test_room_data.copy()
        room_data["room_number"] = unique_room_number

        # First create a room
        response = self.session.post(
            f"{BASE_URL}/rooms",
            json=room_data,
            headers={"Content-Type": "application/json"}
        )
        # Debug: Print response for troubleshooting
        if response.status_code != 201:
            print(f"First room creation failed: {response.status_code} - {response.text}")

        self.assertEqual(response.status_code, 201)
        room_data = response.json()

        # Try to create another room with same number
        duplicate_room_data = self.test_room_data.copy()
        duplicate_room_data["room_number"] = unique_room_number

        response = self.session.post(
            f"{BASE_URL}/rooms",
            json=duplicate_room_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 400)

        # Cleanup - store the created room ID
        self.test_room_id = room_data["id"]

    def test_update_and_delete_room(self):
        """Test updating and deleting a room"""
        room_data = self.test_room_data.copy()
        room_data["room_number"] = f"UPD_DEL_{int(time.time())}"
        update_data = {"capacity": 4}
        response = self.session.put(
            f"{BASE_URL}/rooms/{room_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        updated_room = response.json()
        self.assertEqual(updated_room["capacity"], 4)

        # Delete
        response = self.session.delete(f"{BASE_URL}/rooms/{room_id}")
        self.assertEqual(response.status_code, 200)

        # Verify deletion
        response = self.session.get(f"{BASE_URL}/rooms/{room_id}")
        self.assertEqual(response.status_code, 404)

    # Guest Tests
    def test_create_and_get_guest(self):
        """Test creating a guest and then retrieving it"""
        # Use unique email to avoid conflicts
        guest_data = self.test_guest_data.copy()
        guest_data["email"] = f"test{int(time.time())}@example.com"

        # POST /api/guests
        response = self.session.post(
            f"{BASE_URL}/guests",
            json=guest_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        guest_data = response.json()
        self.assertIn("id", guest_data)

        # GET /api/guests/{guest_id}
        guest_id = guest_data["id"]
        response = self.session.get(f"{BASE_URL}/guests/{guest_id}")
        self.assertEqual(response.status_code, 200)
        retrieved_guest = response.json()
        self.assertEqual(retrieved_guest["first_name"], guest_data["first_name"])

        # Store guest ID for later tests
        self.test_guest_id = guest_id

    def test_search_guests(self):
        """Test guest search functionality"""
        # First create a guest with unique data
        guest_data = self.test_guest_data.copy()
        guest_data["email"] = f"searchtest{int(time.time())}@example.com"

        response = self.session.post(
            f"{BASE_URL}/guests",
            json=guest_data,
            headers={"Content-Type": "application/json"}
        )
        guest_data = response.json()

        # GET /api/guests/search?q=Test
        response = self.session.get(f"{BASE_URL}/guests/search", params={"q": "Test"})
        self.assertEqual(response.status_code, 200)
        search_results = response.json()
        self.assertIsInstance(search_results, list)
        self.assertTrue(len(search_results) >= 1)

        # Store guest ID
        self.test_guest_id = guest_data["id"]

    def test_update_and_delete_guest(self):
        """Test updating and deleting a guest"""
        guest_data = self.test_guest_data.copy()
        guest_data["email"] = f"upddel{int(time.time())}@example.com"

        response = self.session.post(
            f"{BASE_URL}/guests",
            json=guest_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        guest_id = response.json()["id"]

        update_data = {"first_name": "UpdatedName"}
        response = self.session.put(
            f"{BASE_URL}/guests/{guest_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["first_name"], "UpdatedName")

        # Delete
        response = self.session.delete(f"{BASE_URL}/guests/{guest_id}")
        self.assertEqual(response.status_code, 200)

    # Room Group Tests
    def test_get_room_groups(self):
        """Test getting room groups"""
        # GET /api/room-groups
        response = self.session.get(f"{BASE_URL}/room-groups")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    def test_create_room_group(self):
        """Test creating a room group"""
        # POST /api/room-groups
        group_data = {
            "name": f"Test Group {int(time.time())}",
            "description": "Test room group"
        }
        response = self.session.post(
            f"{BASE_URL}/room-groups",
            json=group_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        group_response = response.json()
        self.assertIn("name", group_response)

    def test_update_and_delete_room_group(self):
        """Test updating and deleting a room group"""
        group_data = {
            "name": f"Group to modify {int(time.time())}",
            "description": "Will be updated"
        }
        response = self.session.post(
            f"{BASE_URL}/room-groups",
            json=group_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        group_id = response.json()["id"]

        # Update
        update_data = {"name": "Updated Group Name"}
        response = self.session.put(
            f"{BASE_URL}/room-groups/{group_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Updated Group Name")

        # Delete
        response = self.session.delete(f"{BASE_URL}/room-groups/{group_id}")
        self.assertEqual(response.status_code, 200)

    # Seasonal Rate Tests
    def test_create_seasonal_rate(self):
        """Test creating a seasonal rate"""
        # POST /api/seasonal-rates
        seasonal_data = {
            "name": f"Test Season {int(time.time())}",
            "start_date": "2024-12-20",
            "end_date": "2024-12-31",
            "rate_multiplier": 1.2,
            "room_type": "test_suite"
        }
        response = self.session.post(
            f"{BASE_URL}/seasonal-rates",
            json=seasonal_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        seasonal_response = response.json()
        self.assertIn("name", seasonal_response)

    def test_get_seasonal_rates(self):
        """Test getting seasonal rates"""
        # GET /api/seasonal-rates
        response = self.session.get(f"{BASE_URL}/seasonal-rates")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)

    # Service Tests
    def test_create_and_get_service(self):
        """Test creating and retrieving services"""
        # POST /api/services
        service_data = {
            "name": f"Test Service {int(time.time())}",
            "description": "Test service description",
            "price": 25.0
        }
        response = self.session.post(
            f"{BASE_URL}/services",
            json=service_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)

        # GET /api/services
        response = self.session.get(f"{BASE_URL}/services")
        self.assertEqual(response.status_code, 200)
        services = response.json()
        self.assertIsInstance(services, list)

    def test_update_and_delete_service(self):
        """Test updating and deleting services"""
        # POST /api/services
        service_data = {
            "name": f"Test Service {int(time.time())}",
            "description": "To be updated",
            "price": 25.0
        }
        response = self.session.post(
            f"{BASE_URL}/services",
            json=service_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        service_id = response.json()["id"]

        # PUT /api/services/{id}
        update_data = {
            "name": "Updated Service Name",
            "price": 30.0
        }
        response = self.session.put(
            f"{BASE_URL}/services/{service_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        updated = response.json()
        self.assertEqual(updated["name"], "Updated Service Name")
        self.assertEqual(updated["price"], 30.0)

        # DELETE /api/services/{id}
        response = self.session.delete(f"{BASE_URL}/services/{service_id}")
        self.assertEqual(response.status_code, 200)

    # Booking Tests
    def test_calculate_booking_rate(self):
        """Test booking rate calculation"""
        # First create a room with unique number
        room_data = self.test_room_data.copy()
        room_data["room_number"] = f"RATECALC{int(time.time())}"

        room_response = self.session.post(
            f"{BASE_URL}/rooms",
            json=room_data,
            headers={"Content-Type": "application/json"}
        )
        # Debug: Print response for troubleshooting
        if room_response.status_code != 201:
            print(f"Room creation for rate calc failed: {room_response.status_code} - {room_response.text}")

        self.assertEqual(room_response.status_code, 201)
        room_data = room_response.json()

        # POST /api/bookings/calculate-rate
        rate_calc_data = {
            "room_id": room_data["id"],
            "check_in": self.test_booking_data["check_in"],
            "check_out": self.test_booking_data["check_out"],
            "number_of_guests": 2
        }
        response = self.session.post(
            f"{BASE_URL}/bookings/calculate-rate",
            json=rate_calc_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        rate_data = response.json()
        self.assertIn("total_amount", rate_data)
        self.assertIn("total_nights", rate_data)

        # Store room ID for cleanup
        self.test_room_id = room_data["id"]

    def test_calculate_booking_rate_capacity_warning(self):
        """Test booking rate calculation with capacity warning"""
        # Create a room with capacity 2
        room_data = self.test_room_data.copy()
        room_data["room_number"] = f"CAPWARN{int(time.time())}"
        room_data["capacity"] = 2

        room_response = self.session.post(
            f"{BASE_URL}/rooms",
            json=room_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(room_response.status_code, 201)
        room_id = room_response.json()["id"]

        # Calculate rate for 3 guests (exceeds capacity)
        rate_calc_data = {
            "room_id": room_id,
            "check_in": self.test_booking_data["check_in"],
            "check_out": self.test_booking_data["check_out"],
            "number_of_guests": 3
        }
        response = self.session.post(
            f"{BASE_URL}/bookings/calculate-rate",
            json=rate_calc_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        rate_data = response.json()
        
        # Verify capacity warning fields
        self.assertTrue(rate_data.get("capacity_exceeded"))
        self.assertEqual(rate_data.get("max_capacity"), 2)

        # Calculate rate for 2 guests (within capacity)
        rate_calc_data["number_of_guests"] = 2
        response = self.session.post(
            f"{BASE_URL}/bookings/calculate-rate",
            json=rate_calc_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        rate_data = response.json()
        self.assertFalse(rate_data.get("capacity_exceeded"))

    def test_create_booking(self):
        """Test creating a booking"""
        # First create a guest and room with unique data
        guest_data = self.test_guest_data.copy()
        guest_data["email"] = f"bookingtest{int(time.time())}@example.com"

        guest_response = self.session.post(
            f"{BASE_URL}/guests",
            json=guest_data,
            headers={"Content-Type": "application/json"}
        )
        guest_data = guest_response.json()

        room_data = self.test_booking_room_data()
        room_response = self.session.post(
            f"{BASE_URL}/rooms",
            json=room_data,
            headers={"Content-Type": "application/json"}
        )
        # Debug: Print response for troubleshooting
        if room_response.status_code != 201:
            print(f"Room creation for booking failed: {room_response.status_code} - {room_response.text}")

        self.assertEqual(room_response.status_code, 201)
        room_data = room_response.json()

        # POST /api/bookings
        booking_data = {
            "guest_id": guest_data["id"],
            "room_id": room_data["id"],
            "check_in": self.test_booking_data["check_in"],
            "check_out": self.test_booking_data["check_out"],
            "number_of_guests": 2,
            "total_amount": 200.0,
            "status": "confirmed"
        }
        response = self.session.post(
            f"{BASE_URL}/bookings",
            json=booking_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        booking_response = response.json()
        self.assertIn("booking_id", booking_response)

        # Store IDs for cleanup
        self.test_guest_id = guest_data["id"]
        self.test_room_id = room_data["id"]
        self.test_booking_id = booking_response["id"]

    def test_update_booking(self):
        """Test updating an existing booking"""
        # Create prerequisite data
        guest_data = self.test_guest_data.copy()
        guest_data["email"] = f"updguest{int(time.time())}@example.com"
        guest_response = self.session.post(
            f"{BASE_URL}/guests", json=guest_data, headers={"Content-Type": "application/json"}
        )
        self.assertEqual(guest_response.status_code, 201)

        # Create a second guest for update testing
        guest_data2 = self.test_guest_data.copy()
        guest_data2["email"] = f"updguest2{int(time.time())}@example.com"
        guest_response2 = self.session.post(
            f"{BASE_URL}/guests", json=guest_data2, headers={"Content-Type": "application/json"}
        )
        self.assertEqual(guest_response2.status_code, 201)

        room_data = self.test_booking_room_data()
        room_data["room_number"] = f"UPDBOOK{int(time.time())}"
        room_response = self.session.post(
            f"{BASE_URL}/rooms", json=room_data, headers={"Content-Type": "application/json"}
        )
        self.assertEqual(room_response.status_code, 201)

        # Create initial booking
        booking_data = {
            "guest_id": guest_response.json()["id"],
            "room_id": room_response.json()["id"],
            "check_in": (date.today() + timedelta(days=20)).isoformat(),
            "check_out": (date.today() + timedelta(days=22)).isoformat(),
            "number_of_guests": 1,
            "status": "confirmed"
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/bookings", json=booking_data, headers={"Content-Type": "application/json"}
        )
        self.assertEqual(create_response.status_code, 201)
        booking_id = create_response.json()['id']
        initial_amount = create_response.json()['total_amount']

        # Update the booking (change dates and guests)
        update_data = {
            "guest_id": guest_response2.json()["id"],
            "check_in": (date.today() + timedelta(days=20)).isoformat(),
            "check_out": (date.today() + timedelta(days=23)).isoformat(),
            "number_of_guests": 2,
            "notes": "Updated notes"
        }
        
        update_response = self.session.put(
            f"{BASE_URL}/bookings/{booking_id}", json=update_data, headers={"Content-Type": "application/json"}
        )
        self.assertEqual(update_response.status_code, 200)
        
        updated_booking = update_response.json()
        self.assertEqual(updated_booking['guest_id'], update_data['guest_id'])
        self.assertEqual(updated_booking['check_out'], update_data['check_out'])
        self.assertEqual(updated_booking['number_of_guests'], 2)
        self.assertEqual(updated_booking['notes'], "Updated notes")
        # Check if amount was recalculated
        self.assertNotEqual(updated_booking['total_amount'], initial_amount)
        # 3 days at 100 = 300
        self.assertEqual(updated_booking['total_amount'], 300.0)

    def test_create_booking_invalid_dates(self):
        """Test creating a booking with check-out date before check-in date"""
        guest_data = self.test_guest_data.copy()
        guest_data["email"] = f"invdate{int(time.time())}@example.com"
        guest_response = self.session.post(
            f"{BASE_URL}/guests", json=guest_data, headers={"Content-Type": "application/json"}
        )
        self.assertEqual(guest_response.status_code, 201)

        room_data = self.test_booking_room_data()
        room_data["room_number"] = f"INVDATE{int(time.time())}"
        room_response = self.session.post(
            f"{BASE_URL}/rooms", json=room_data, headers={"Content-Type": "application/json"}
        )
        self.assertEqual(room_response.status_code, 201)

        invalid_booking_data = {
            "guest_id": guest_response.json()["id"],
            "room_id": room_response.json()["id"],
            "check_in": (date.today() + timedelta(days=3)).isoformat(),
            "check_out": (date.today() + timedelta(days=1)).isoformat(),
            "number_of_guests": 2,
            "status": "confirmed"
        }
        res = self.session.post(
            f"{BASE_URL}/bookings", json=invalid_booking_data, headers={"Content-Type": "application/json"}
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("must be after check-in date", res.json().get("error", ""))

    def test_get_bookings_with_filters(self):
        """Test getting bookings with various filters"""
        # GET /api/bookings?status=confirmed
        response = self.session.get(f"{BASE_URL}/bookings", params={"status": "confirmed"})
        self.assertEqual(response.status_code, 200)
        bookings = response.json()
        self.assertIsInstance(bookings, list)

        # GET /api/bookings with date filter
        today = date.today().isoformat()
        response = self.session.get(f"{BASE_URL}/bookings", params={"date": today})
        self.assertEqual(response.status_code, 200)

    # Availability Tests
    def test_get_availability(self):
        """Test room availability checking"""
        # GET /api/availability?start_date=2024-12-01&end_date=2024-12-07
        start_date = (date.today() + timedelta(days=10)).isoformat()
        end_date = (date.today() + timedelta(days=17)).isoformat()

        response = self.session.get(
            f"{BASE_URL}/availability",
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )
        self.assertEqual(response.status_code, 200)
        availability_data = response.json()
        self.assertIsInstance(availability_data, list)

    def test_calendar_views(self):
        """Test weekly and monthly calendar views"""
        # GET /api/calendar/weekly
        response = self.session.get(f"{BASE_URL}/calendar/weekly")
        self.assertEqual(response.status_code, 200)
        weekly_data = response.json()
        self.assertIn("week_start", weekly_data)
        self.assertIn("rooms", weekly_data)

        # GET /api/calendar/monthly
        response = self.session.get(f"{BASE_URL}/calendar/monthly")
        self.assertEqual(response.status_code, 200)
        monthly_data = response.json()
        self.assertIn("year", monthly_data)
        self.assertIn("month", monthly_data)

    # Event Tests
    def test_create_and_get_event(self):
        """Test creating and retrieving events"""
        # POST /api/events
        event_data = {
            "name": f"Test Event {int(time.time())}",
            "event_date": (date.today() + timedelta(days=5)).isoformat(),
            "space": "Conference Room",
            "status": "confirmed",
            "expected_guests": 50
        }
        response = self.session.post(
            f"{BASE_URL}/events",
            json=event_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        event_response = response.json()

        # GET /api/events
        response = self.session.get(f"{BASE_URL}/events")
        self.assertEqual(response.status_code, 200)
        events = response.json()
        self.assertIsInstance(events, list)

    # Housekeeping Tests
    def test_create_housekeeping_record(self):
        """Test creating housekeeping records"""
        # First create a room with unique number
        room_data = self.test_room_data.copy()
        room_data["room_number"] = f"HKEEP{int(time.time())}"

        room_response = self.session.post(
            f"{BASE_URL}/rooms",
            json=room_data,
            headers={"Content-Type": "application/json"}
        )
        # Debug: Print response for troubleshooting
        if room_response.status_code != 201:
            print(f"Room creation for housekeeping failed: {room_response.status_code} - {room_response.text}")

        self.assertEqual(room_response.status_code, 201)
        room_data = room_response.json()

        # Verify room_data has 'id'
        self.assertIn("id", room_data)
        room_id = room_data["id"]

        # POST /api/housekeeping
        housekeeping_data = {
            "room_id": room_id,
            "status": "clean",
            "last_cleaned": date.today().isoformat(),
            "cleaner": "Test Cleaner"
        }
        response = self.session.post(
            f"{BASE_URL}/housekeeping",
            json=housekeeping_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)

        # Store room ID for cleanup
        self.test_room_id = room_id

    # Maintenance Tests
    def test_create_maintenance_ticket(self):
        """Test creating maintenance tickets"""
        # POST /api/maintenance
        maintenance_data = {
            "area": f"Test Area {int(time.time())}",
            "issue": "Test issue description",
            "priority": "medium",
            "status": "new",
            "assigned_to": "Test Technician"
        }
        response = self.session.post(
            f"{BASE_URL}/maintenance",
            json=maintenance_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)
        maintenance_response = response.json()
        self.assertIn("ticket_id", maintenance_response)

    # Contact Tests
    def test_create_and_get_contact(self):
        """Test creating and retrieving contacts"""
        # POST /api/contacts
        contact_data = {
            "role": f"Test Role {int(time.time())}",
            "name": "Test Contact",
            "phone": "123-456-7890",
            "email": f"contact{int(time.time())}@test.com",
            "on_call": True
        }
        response = self.session.post(
            f"{BASE_URL}/contacts",
            json=contact_data,
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 201)

        # GET /api/contacts
        response = self.session.get(f"{BASE_URL}/contacts")
        self.assertEqual(response.status_code, 200)
        contacts = response.json()
        self.assertIsInstance(contacts, list)

    # Statistics Tests
    def test_get_statistics(self):
        """Test statistics endpoints"""
        # GET /api/statistics/occupancy
        response = self.session.get(f"{BASE_URL}/statistics/occupancy")
        self.assertEqual(response.status_code, 200)
        stats_data = response.json()
        self.assertIn("occupancy_rate", stats_data)

        # GET /api/statistics/yearly-summary
        response = self.session.get(f"{BASE_URL}/statistics/yearly-summary")
        self.assertEqual(response.status_code, 200)
        yearly_data = response.json()
        self.assertIn("year", yearly_data)

    # Error Handling Tests
    def test_nonexistent_endpoint(self):
        """Test handling of non-existent endpoints"""
        response = self.session.get(f"{BASE_URL}/nonexistent")
        self.assertEqual(response.status_code, 404)

    def test_invalid_room_id(self):
        """Test handling of invalid room ID"""
        response = self.session.get(f"{BASE_URL}/rooms/99999")
        self.assertEqual(response.status_code, 404)

    # Helper Methods
    def test_booking_room_data(self):
        """Helper method to get unique room data for booking tests"""
        return {
            "room_number": f"BOOK{int(time.time())}",
            "room_type": "booking_test",
            "capacity": 2,
            "base_rate": 100.0
        }


def run_tests():
    """Run the test suite"""
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMiniHotelAPI)

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"TEST SUMMARY:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"{'=' * 50}")

    return result.wasSuccessful()


if __name__ == "__main__":
    print("MiniHotel API Test Suite")
    print("Make sure the API server is running before executing tests!")
    print(f"Testing against: {BASE_URL}")
    print("=" * 50)

    success = run_tests()

    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)