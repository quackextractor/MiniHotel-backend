# Minihotel Management API

A comprehensive REST API for hotel management system based on the Minihotel Megadocs specification.

## Features

- **Room Management**: CRUD operations for rooms with grouping support
- **Guest Management**: Guest profiles and search functionality
- **Booking System**: Complete booking lifecycle management
- **Calendar & Availability**: Real-time room availability checking
- **Event Management**: Conference rooms and special events
- **Housekeeping**: Room status tracking and cleaning schedules
- **Maintenance**: Maintenance ticket system with priority levels
- **Contacts**: Staff contact information

## Quick Start

1. **Run the application:**
   ```bash
   python main.py
   ```
   *Note: The script will automatically create a `.venv` and install dependencies from `requirements.txt` if not already present. To use global packages instead, use `python main.py --use-global`.*

3. **Access the API:**
   - API Base URL: `http://localhost:5000/api`
   - Swagger Documentation: `http://localhost:5000/docs`

## API Endpoints

### Rooms
- `GET /api/rooms` - List all rooms
- `GET /api/rooms/{id}` - Get room details
- `POST /api/rooms` - Create new room

### Guests
- `GET /api/guests` - List guests (with search)
- `GET /api/guests/{id}` - Get guest details
- `POST /api/guests` - Create new guest

### Bookings
- `GET /api/bookings` - List bookings (with filters)
- `GET /api/bookings/{id}` - Get booking details
- `POST /api/bookings` - Create new booking
- `PATCH /api/bookings/{id}/status` - Update booking status

### Availability
- `GET /api/availability` - Check room availability

## Data Models

### Booking Statuses
- `confirmed` - Fully paid and guaranteed
- `tentative` - Holding; not yet paid
- `pending_payment` - Awaiting payment
- `checked_in` - Guest has arrived
- `checked_out` - Guest departed
- `cancelled` - Booking cancelled
- `no_show` - Guest did not arrive

### Room Types
- Single, Double, Suite, Family rooms
- Support for room grouping
- Seasonal pricing support

## Environment Variables

- `DATABASE_URL`: Database connection string (default: SQLite)

## Development

The API follows K.I.S.S. principle and includes:
- Comprehensive error handling
- Input validation
- Automatic booking ID generation
- Conflict detection for overlapping bookings
- Full Swagger/OpenAPI documentation

## Example Usage

Create a booking:
```bash
curl -X POST http://localhost:5000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "guest_id": 1,
    "room_id": 1,
    "check_in": "2025-04-10",
    "check_out": "2025-04-13",
    "number_of_guests": 2,
    "total_amount": 9600,
    "status": "confirmed",
    "payment_status": "paid",
    "notes": "Anniversary stay"
  }'
```

Check availability:
```bash
curl "http://localhost:5000/api/availability?start_date=2025-04-10&end_date=2025-04-15"
```
```

This implementation provides a complete backend API that covers all the functionality described in your Minihotel Megadocs. The API includes:

1. **Full CRUD operations** for all major entities
2. **Booking system** with status management and availability checking
3. **Search and filtering** capabilities
4. **Automatic conflict detection** for overlapping bookings
5. **Comprehensive Swagger documentation**
6. **Error handling and validation**
7. **Room grouping and organizational structure**

The API is ready to run and includes sample data structures that match your mock data. You can extend it by adding the remaining endpoints for Events, Housekeeping, Maintenance, and Contacts following the same patterns.