import os
from datetime import datetime, date, timedelta

from flask import Flask, request, jsonify
from flask_cors import CORS

from database import db, Room, Guest, Booking, Event, Housekeeping, Maintenance, Contact, RoomGroup, SeasonalRate, \
    Service, BookingService
from schemas import (
    room_schema, rooms_schema, guest_schema, guests_schema,
    booking_schema, bookings_schema, event_schema, events_schema,
    housekeeping_schema, housekeepings_schema, maintenance_schema,
    maintenances_schema, contact_schema, contacts_schema,
    room_group_schema, room_groups_schema, seasonal_rate_schema, seasonal_rates_schema,
    service_schema, services_schema, booking_service_schema
)


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///minihotel.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Create tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint
    ---
    responses:
      200:
        description: API is running
    """
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


# Room endpoints
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """Get all rooms
    ---
    parameters:
      - name: active
        in: query
        type: boolean
        required: false
        description: Filter by active status
    responses:
      200:
        description: List of rooms
    """
    active_only = request.args.get('active', 'true').lower() == 'true'
    query = Room.query
    if active_only:
        query = query.filter_by(is_active=True)
    rooms = query.all()
    return jsonify(rooms_schema.dump(rooms))


@app.route('/api/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    """Get room by ID
    ---
    parameters:
      - name: room_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Room data
      404:
        description: Room not found
    """
    room = Room.query.get_or_404(room_id)
    return jsonify(room_schema.dump(room))


@app.route('/api/rooms', methods=['POST'])
def create_room():
    """Create a new room
    ---
    parameters:
      - in: body
        name: room
        schema:
          type: object
          required:
            - room_number
            - room_type
            - capacity
            - base_rate
          properties:
            room_number:
              type: string
            room_type:
              type: string
            description:
              type: string
            capacity:
              type: integer
            base_rate:
              type: number
            group_id:
              type: integer
    responses:
      201:
        description: Room created
      400:
        description: Invalid data
    """
    data = request.get_json()

    # Check if room number already exists
    if Room.query.filter_by(room_number=data.get('room_number')).first():
        return jsonify({'error': 'Room number already exists'}), 400

    room = Room(
        room_number=data['room_number'],
        room_type=data['room_type'],
        description=data.get('description'),
        capacity=data['capacity'],
        base_rate=data['base_rate'],
        group_id=data.get('group_id'),
        is_active=data.get('is_active', True)
    )

    db.session.add(room)
    db.session.commit()

    return jsonify(room_schema.dump(room)), 201


# Room Group endpoints
@app.route('/api/room-groups', methods=['GET'])
def get_room_groups():
    """Get all room groups in tree structure
    ---
    responses:
      200:
        description: List of room groups
    """
    groups = RoomGroup.query.filter_by(parent_group_id=None).all()
    return jsonify(room_groups_schema.dump(groups))


@app.route('/api/room-groups', methods=['POST'])
def create_room_group():
    """Create a new room group
    ---
    parameters:
      - in: body
        name: room_group
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
            description:
              type: string
            parent_group_id:
              type: integer
    responses:
      201:
        description: Room group created
      400:
        description: Invalid data
    """
    data = request.get_json()

    group = RoomGroup(
        name=data['name'],
        description=data.get('description'),
        parent_group_id=data.get('parent_group_id')
    )

    db.session.add(group)
    db.session.commit()

    return jsonify(room_group_schema.dump(group)), 201


# Seasonal Rates endpoints
@app.route('/api/seasonal-rates', methods=['GET'])
def get_seasonal_rates():
    """Get all seasonal rates
    ---
    responses:
      200:
        description: List of seasonal rates
    """
    rates = SeasonalRate.query.all()
    return jsonify(seasonal_rates_schema.dump(rates))


@app.route('/api/seasonal-rates', methods=['POST'])
def create_seasonal_rate():
    """Create a new seasonal rate
    ---
    parameters:
      - in: body
        name: seasonal_rate
        schema:
          type: object
          required:
            - name
            - start_date
            - end_date
            - rate_multiplier
          properties:
            name:
              type: string
            start_date:
              type: string
              format: date
            end_date:
              type: string
              format: date
            rate_multiplier:
              type: number
            room_type:
              type: string
            room_group_id:
              type: integer
    responses:
      201:
        description: Seasonal rate created
      400:
        description: Invalid data
    """
    data = request.get_json()

    rate = SeasonalRate(
        name=data['name'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
        rate_multiplier=data['rate_multiplier'],
        room_type=data.get('room_type'),
        room_group_id=data.get('room_group_id')
    )

    db.session.add(rate)
    db.session.commit()

    return jsonify(seasonal_rate_schema.dump(rate)), 201


# Services endpoints
@app.route('/api/services', methods=['GET'])
def get_services():
    """Get all active services
    ---
    responses:
      200:
        description: List of services
    """
    services = Service.query.filter_by(is_active=True).all()
    return jsonify(services_schema.dump(services))


@app.route('/api/services', methods=['POST'])
def create_service():
    """Create a new service
    ---
    parameters:
      - in: body
        name: service
        schema:
          type: object
          required:
            - name
            - price
          properties:
            name:
              type: string
            description:
              type: string
            price:
              type: number
    responses:
      201:
        description: Service created
      400:
        description: Invalid data
    """
    data = request.get_json()

    service = Service(
        name=data['name'],
        description=data.get('description'),
        price=data['price']
    )

    db.session.add(service)
    db.session.commit()

    return jsonify(service_schema.dump(service)), 201


# Guest endpoints
@app.route('/api/guests', methods=['GET'])
def get_guests():
    """Get all guests
    ---
    parameters:
      - name: search
        in: query
        type: string
        required: false
        description: Search by last name, first name, or email
    responses:
      200:
        description: List of guests
    """
    search = request.args.get('search')
    query = Guest.query

    if search:
        query = query.filter(
            (Guest.last_name.ilike(f'%{search}%')) |
            (Guest.first_name.ilike(f'%{search}%')) |
            (Guest.email.ilike(f'%{search}%'))
        )

    guests = query.all()
    return jsonify(guests_schema.dump(guests))


@app.route('/api/guests/<int:guest_id>', methods=['GET'])
def get_guest(guest_id):
    """Get guest by ID
    ---
    parameters:
      - name: guest_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Guest data
      404:
        description: Guest not found
    """
    guest = Guest.query.get_or_404(guest_id)
    return jsonify(guest_schema.dump(guest))


@app.route('/api/guests', methods=['POST'])
def create_guest():
    """Create a new guest
    ---
    parameters:
      - in: body
        name: guest
        schema:
          type: object
          required:
            - first_name
            - last_name
          properties:
            first_name:
              type: string
            last_name:
              type: string
            email:
              type: string
            phone:
              type: string
            address:
              type: string
    responses:
      201:
        description: Guest created
      400:
        description: Invalid data
    """
    data = request.get_json()

    guest = Guest(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address')
    )

    db.session.add(guest)
    db.session.commit()

    return jsonify(guest_schema.dump(guest)), 201


# Enhanced guest search endpoint
@app.route('/api/guests/search', methods=['GET'])
def search_guests():
    """Enhanced guest search by name, email, or phone
    ---
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search query
    responses:
      200:
        description: List of matching guests
    """
    query = request.args.get('q', '')

    if not query:
        return jsonify([])

    guests = Guest.query.filter(
        (Guest.first_name.ilike(f'%{query}%')) |
        (Guest.last_name.ilike(f'%{query}%')) |
        (Guest.email.ilike(f'%{query}%')) |
        (Guest.phone.ilike(f'%{query}%'))
    ).all()

    return jsonify(guests_schema.dump(guests))


# Guest booking history endpoint
@app.route('/api/guests/<int:guest_id>/bookings', methods=['GET'])
def get_guest_bookings(guest_id):
    """Get booking history for a specific guest
    ---
    parameters:
      - name: guest_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: List of guest's bookings
      404:
        description: Guest not found
    """
    guest = Guest.query.get_or_404(guest_id)
    bookings = Booking.query.filter_by(guest_id=guest_id).order_by(Booking.created_at.desc()).all()
    return jsonify(bookings_schema.dump(bookings))


# Booking endpoints
@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings with optional filters
    ---
    parameters:
      - name: status
        in: query
        type: string
        required: false
        description: Filter by status
      - name: date
        in: query
        type: string
        required: false
        description: Filter by date (YYYY-MM-DD)
      - name: guest_name
        in: query
        type: string
        required: false
        description: Search by guest name
      - name: room_id
        in: query
        type: integer
        required: false
        description: Filter by room ID
    responses:
      200:
        description: List of bookings
    """
    status = request.args.get('status')
    date_str = request.args.get('date')
    guest_name = request.args.get('guest_name')
    room_id = request.args.get('room_id')

    query = Booking.query.join(Guest)

    if status:
        query = query.filter(Booking.status == status)

    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(Booking.check_in <= filter_date, Booking.check_out >= filter_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    if guest_name:
        query = query.filter(
            (Guest.first_name.ilike(f'%{guest_name}%')) |
            (Guest.last_name.ilike(f'%{guest_name}%'))
        )

    if room_id:
        query = query.filter(Booking.room_id == room_id)

    bookings = query.all()
    return jsonify(bookings_schema.dump(bookings))


@app.route('/api/bookings/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get booking by ID
    ---
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Booking data
      404:
        description: Booking not found
    """
    booking = Booking.query.get_or_404(booking_id)
    return jsonify(booking_schema.dump(booking))


@app.route('/api/bookings/calculate-rate', methods=['POST'])
def calculate_booking_rate():
    """Calculate booking rate considering seasonal rates and number of guests
    ---
    parameters:
      - in: body
        name: rate_calculation
        schema:
          type: object
          required:
            - room_id
            - check_in
            - check_out
          properties:
            room_id:
              type: integer
            check_in:
              type: string
              format: date
            check_out:
              type: string
              format: date
            number_of_guests:
              type: integer
    responses:
      200:
        description: Rate calculation result
      404:
        description: Room not found
    """
    data = request.get_json()

    room_id = data['room_id']
    check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
    check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
    number_of_guests = data.get('number_of_guests', 1)

    room = Room.query.get_or_404(room_id)

    # Calculate base rate
    total_nights = (check_out - check_in).days
    base_amount = room.base_rate * total_nights

    # Apply seasonal rates if any
    current_date = check_in
    seasonal_adjustment = 0

    while current_date < check_out:
        # Check for seasonal rates for this date
        seasonal_rate = SeasonalRate.query.filter(
            SeasonalRate.start_date <= current_date,
            SeasonalRate.end_date >= current_date,
            (SeasonalRate.room_type == room.room_type) | (SeasonalRate.room_type.is_(None))
        ).first()

        if seasonal_rate:
            daily_rate = room.base_rate * (seasonal_rate.rate_multiplier - 1.0)
            seasonal_adjustment += daily_rate

        current_date += timedelta(days=1)

    # Apply capacity-based pricing (simple implementation)
    capacity_multiplier = 1.0
    if number_of_guests > 2:  # Example: charge 20% more for extra guests
        capacity_multiplier = 1.0 + (number_of_guests - 2) * 0.2

    total_amount = (base_amount + seasonal_adjustment) * capacity_multiplier

    return jsonify({
        'base_amount': base_amount,
        'seasonal_adjustment': seasonal_adjustment,
        'capacity_multiplier': capacity_multiplier,
        'total_amount': round(total_amount, 2),
        'total_nights': total_nights
    })


@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Create a new booking
    ---
    parameters:
      - in: body
        name: booking
        schema:
          type: object
          required:
            - guest_id
            - room_id
            - check_in
            - check_out
            - number_of_guests
          properties:
            guest_id:
              type: integer
            room_id:
              type: integer
            check_in:
              type: string
              format: date
            check_out:
              type: string
              format: date
            number_of_guests:
              type: integer
            total_amount:
              type: number
            status:
              type: string
            payment_status:
              type: string
            payment_method:
              type: string
            notes:
              type: string
            assigned_to:
              type: string
            recreational_fee:
              type: number
            consumed_amount:
              type: number
    responses:
      201:
        description: Booking created
      400:
        description: Invalid data or room not available
    """
    data = request.get_json()

    # Check room availability (skip for draft status)
    status = data.get('status', 'confirmed')
    if status not in ['draft', 'tentative']:
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()

        conflicting_booking = Booking.query.filter(
            Booking.room_id == data['room_id'],
            Booking.status.in_(['confirmed', 'checked_in', 'pending_payment']),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).first()

        if conflicting_booking:
            return jsonify({'error': 'Room not available for the selected dates'}), 400

    # Generate booking ID
    last_booking = Booking.query.order_by(Booking.id.desc()).first()
    new_id = last_booking.id + 1 if last_booking else 1
    booking_id = f"BKG-{new_id:04d}"

    booking = Booking(
        booking_id=booking_id,
        guest_id=data['guest_id'],
        room_id=data['room_id'],
        check_in=datetime.strptime(data['check_in'], '%Y-%m-%d').date(),
        check_out=datetime.strptime(data['check_out'], '%Y-%m-%d').date(),
        number_of_guests=data['number_of_guests'],
        total_amount=data.get('total_amount', 0),
        status=status,
        payment_status=data.get('payment_status', 'not_paid'),
        payment_method=data.get('payment_method'),
        notes=data.get('notes'),
        assigned_to=data.get('assigned_to'),
        recreational_fee=data.get('recreational_fee', 0.0),
        consumed_amount=data.get('consumed_amount', 0.0)
    )

    db.session.add(booking)
    db.session.commit()

    return jsonify(booking_schema.dump(booking)), 201


@app.route('/api/bookings/<int:booking_id>/status', methods=['PATCH'])
def update_booking_status(booking_id):
    """Update booking status
    ---
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
      - in: body
        name: status_update
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
            payment_status:
              type: string
    responses:
      200:
        description: Status updated
      404:
        description: Booking not found
    """
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json()

    if 'status' in data:
        booking.status = data['status']

    if 'payment_status' in data:
        booking.payment_status = data['payment_status']

    db.session.commit()

    return jsonify(booking_schema.dump(booking))


# Booking Services endpoints
@app.route('/api/bookings/<int:booking_id>/services', methods=['POST'])
def add_booking_service(booking_id):
    """Add a service to a booking
    ---
    parameters:
      - name: booking_id
        in: path
        type: integer
        required: true
      - in: body
        name: booking_service
        schema:
          type: object
          required:
            - service_id
            - date
          properties:
            service_id:
              type: integer
            quantity:
              type: integer
            date:
              type: string
              format: date
    responses:
      201:
        description: Service added to booking
      404:
        description: Booking or service not found
    """
    data = request.get_json()

    # Check if booking exists
    booking = Booking.query.get_or_404(booking_id)
    # Check if service exists
    service = Service.query.get_or_404(data['service_id'])

    booking_service = BookingService(
        booking_id=booking_id,
        service_id=data['service_id'],
        quantity=data.get('quantity', 1),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    )

    db.session.add(booking_service)
    db.session.commit()

    return jsonify(booking_service_schema.dump(booking_service)), 201


# Calendar availability endpoint
@app.route('/api/availability', methods=['GET'])
def get_availability():
    """Get room availability for a date range
    ---
    parameters:
      - name: start_date
        in: query
        type: string
        required: true
        description: Start date (YYYY-MM-DD)
      - name: end_date
        in: query
        type: string
        required: true
        description: End date (YYYY-MM-DD)
      - name: room_type
        in: query
        type: string
        required: false
        description: Filter by room type
    responses:
      200:
        description: Availability data
      400:
        description: Invalid date range
    """
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    room_type = request.args.get('room_type')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    query = Room.query.filter_by(is_active=True)
    if room_type:
        query = query.filter_by(room_type=room_type)

    rooms = query.all()
    availability = []

    for room in rooms:
        # Check for conflicting bookings
        conflicting_booking = Booking.query.filter(
            Booking.room_id == room.id,
            Booking.status.in_(['confirmed', 'checked_in', 'pending_payment']),
            Booking.check_in < end_date,
            Booking.check_out > start_date
        ).first()

        is_available = conflicting_booking is None

        availability.append({
            'room_id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'capacity': room.capacity,
            'base_rate': room.base_rate,
            'available': is_available,
            'conflicting_booking': booking_schema.dump(conflicting_booking) if conflicting_booking else None
        })

    return jsonify(availability)


# Weekly calendar view
@app.route('/api/calendar/weekly', methods=['GET'])
def get_weekly_calendar():
    """Get weekly calendar view
    ---
    parameters:
      - name: start_date
        in: query
        type: string
        required: false
        description: Start date of the week (YYYY-MM-DD), defaults to current week
    responses:
      200:
        description: Weekly calendar data
    """
    start_date_str = request.args.get('start_date')

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    else:
        start_date = date.today()

    # Adjust to Monday of the week
    start_date = start_date - timedelta(days=start_date.weekday())
    end_date = start_date + timedelta(days=6)

    # Get all rooms
    rooms = Room.query.filter_by(is_active=True).all()

    # Get bookings for the week
    bookings = Booking.query.filter(
        Booking.check_in <= end_date,
        Booking.check_out >= start_date
    ).all()

    # Structure data for weekly view
    calendar_data = {
        'week_start': start_date.isoformat(),
        'week_end': end_date.isoformat(),
        'rooms': [],
        'days': [(start_date + timedelta(days=i)).isoformat() for i in range(7)]
    }

    for room in rooms:
        room_data = {
            'room_id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'capacity': room.capacity,
            'group_name': room.group.name if room.group else None,
            'bookings': []
        }

        # Find bookings for this room in the current week
        room_bookings = [b for b in bookings if b.room_id == room.id]

        for booking in room_bookings:
            room_data['bookings'].append(booking_schema.dump(booking))

        calendar_data['rooms'].append(room_data)

    return jsonify(calendar_data)


# Monthly calendar view
@app.route('/api/calendar/monthly', methods=['GET'])
def get_monthly_calendar():
    """Get monthly calendar view
    ---
    parameters:
      - name: year
        in: query
        type: integer
        required: false
        description: Year (defaults to current year)
      - name: month
        in: query
        type: integer
        required: false
        description: Month (1-12, defaults to current month)
    responses:
      200:
        description: Monthly calendar data
    """
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Get all rooms
    rooms = Room.query.filter_by(is_active=True).all()

    # Get bookings for the month
    bookings = Booking.query.filter(
        Booking.check_in < end_date,
        Booking.check_out >= start_date
    ).all()

    # Structure data for monthly view
    calendar_data = {
        'year': year,
        'month': month,
        'rooms': []
    }

    for room in rooms:
        room_data = {
            'room_id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'bookings': []
        }

        # Find bookings for this room in the current month
        room_bookings = [b for b in bookings if b.room_id == room.id]

        for booking in room_bookings:
            room_data['bookings'].append(booking_schema.dump(booking))

        calendar_data['rooms'].append(room_data)

    return jsonify(calendar_data)


# Event endpoints
@app.route('/api/events', methods=['GET'])
def get_events():
    """Get all events
    ---
    parameters:
      - name: status
        in: query
        type: string
        required: false
        description: Filter by status
      - name: date
        in: query
        type: string
        required: false
        description: Filter by date (YYYY-MM-DD)
    responses:
      200:
        description: List of events
    """
    status = request.args.get('status')
    date_str = request.args.get('date')

    query = Event.query

    if status:
        query = query.filter(Event.status == status)

    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(Event.event_date == filter_date)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    events = query.all()
    return jsonify(events_schema.dump(events))


@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get event by ID
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Event data
      404:
        description: Event not found
    """
    event = Event.query.get_or_404(event_id)
    return jsonify(event_schema.dump(event))


@app.route('/api/events', methods=['POST'])
def create_event():
    """Create a new event
    ---
    parameters:
      - in: body
        name: event
        schema:
          type: object
          required:
            - name
            - event_date
            - space
            - status
          properties:
            name:
              type: string
            event_date:
              type: string
              format: date
            space:
              type: string
            expected_guests:
              type: integer
            status:
              type: string
            contact_email:
              type: string
            contact_phone:
              type: string
            notes:
              type: string
    responses:
      201:
        description: Event created
      400:
        description: Invalid data
    """
    data = request.get_json()

    # Generate event ID
    last_event = Event.query.order_by(Event.id.desc()).first()
    new_id = last_event.id + 1 if last_event else 1
    event_id = f"EVT-{new_id:04d}"

    event = Event(
        event_id=event_id,
        name=data['name'],
        event_date=datetime.strptime(data['event_date'], '%Y-%m-%d').date(),
        space=data['space'],
        expected_guests=data.get('expected_guests'),
        status=data['status'],
        contact_email=data.get('contact_email'),
        contact_phone=data.get('contact_phone'),
        notes=data.get('notes')
    )

    db.session.add(event)
    db.session.commit()

    return jsonify(event_schema.dump(event)), 201


# Housekeeping endpoints
@app.route('/api/housekeeping', methods=['GET'])
def get_housekeeping():
    """Get all housekeeping records
    ---
    parameters:
      - name: room_id
        in: query
        type: integer
        required: false
        description: Filter by room ID
      - name: status
        in: query
        type: string
        required: false
        description: Filter by status
    responses:
      200:
        description: List of housekeeping records
    """
    room_id = request.args.get('room_id')
    status = request.args.get('status')

    query = Housekeeping.query

    if room_id:
        query = query.filter_by(room_id=room_id)

    if status:
        query = query.filter_by(status=status)

    records = query.all()
    return jsonify(housekeepings_schema.dump(records))


@app.route('/api/housekeeping/<int:record_id>', methods=['GET'])
def get_housekeeping_record(record_id):
    """Get housekeeping record by ID
    ---
    parameters:
      - name: record_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Housekeeping record data
      404:
        description: Record not found
    """
    record = Housekeeping.query.get_or_404(record_id)
    return jsonify(housekeeping_schema.dump(record))


@app.route('/api/housekeeping', methods=['POST'])
def create_housekeeping():
    """Create a new housekeeping record
    ---
    parameters:
      - in: body
        name: housekeeping
        schema:
          type: object
          required:
            - room_id
            - status
          properties:
            room_id:
              type: integer
            status:
              type: string
            last_cleaned:
              type: string
              format: date
            cleaner:
              type: string
            notes:
              type: string
    responses:
      201:
        description: Housekeeping record created
      400:
        description: Invalid data
    """
    data = request.get_json()

    record = Housekeeping(
        room_id=data['room_id'],
        status=data['status'],
        last_cleaned=datetime.strptime(data['last_cleaned'], '%Y-%m-%d').date() if data.get('last_cleaned') else None,
        cleaner=data.get('cleaner'),
        notes=data.get('notes')
    )

    db.session.add(record)
    db.session.commit()

    return jsonify(housekeeping_schema.dump(record)), 201


# Maintenance endpoints
@app.route('/api/maintenance', methods=['GET'])
def get_maintenance():
    """Get all maintenance tickets
    ---
    parameters:
      - name: status
        in: query
        type: string
        required: false
        description: Filter by status
      - name: priority
        in: query
        type: string
        required: false
        description: Filter by priority
    responses:
      200:
        description: List of maintenance tickets
    """
    status = request.args.get('status')
    priority = request.args.get('priority')

    query = Maintenance.query

    if status:
        query = query.filter_by(status=status)

    if priority:
        query = query.filter_by(priority=priority)

    tickets = query.all()
    return jsonify(maintenances_schema.dump(tickets))


@app.route('/api/maintenance/<int:ticket_id>', methods=['GET'])
def get_maintenance_ticket(ticket_id):
    """Get maintenance ticket by ID
    ---
    parameters:
      - name: ticket_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Maintenance ticket data
      404:
        description: Ticket not found
    """
    ticket = Maintenance.query.get_or_404(ticket_id)
    return jsonify(maintenance_schema.dump(ticket))


@app.route('/api/maintenance', methods=['POST'])
def create_maintenance():
    """Create a new maintenance ticket
    ---
    parameters:
      - in: body
        name: maintenance
        schema:
          type: object
          required:
            - area
            - issue
            - priority
            - status
          properties:
            area:
              type: string
            issue:
              type: string
            priority:
              type: string
            status:
              type: string
            assigned_to:
              type: string
            notes:
              type: string
    responses:
      201:
        description: Maintenance ticket created
      400:
        description: Invalid data
    """
    data = request.get_json()

    # Generate ticket ID
    last_ticket = Maintenance.query.order_by(Maintenance.id.desc()).first()
    new_id = last_ticket.id + 1 if last_ticket else 1
    ticket_id = f"MT-{new_id:03d}"

    ticket = Maintenance(
        ticket_id=ticket_id,
        area=data['area'],
        issue=data['issue'],
        reported_date=date.today(),
        priority=data['priority'],
        status=data['status'],
        assigned_to=data.get('assigned_to'),
        notes=data.get('notes')
    )

    db.session.add(ticket)
    db.session.commit()

    return jsonify(maintenance_schema.dump(ticket)), 201


# Contact endpoints
@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts
    ---
    parameters:
      - name: role
        in: query
        type: string
        required: false
        description: Filter by role
      - name: on_call
        in: query
        type: boolean
        required: false
        description: Filter by on-call status
    responses:
      200:
        description: List of contacts
    """
    role = request.args.get('role')
    on_call = request.args.get('on_call')

    query = Contact.query

    if role:
        query = query.filter_by(role=role)

    if on_call:
        query = query.filter_by(on_call=on_call.lower() == 'true')

    contacts = query.all()
    return jsonify(contacts_schema.dump(contacts))


@app.route('/api/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get contact by ID
    ---
    parameters:
      - name: contact_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Contact data
      404:
        description: Contact not found
    """
    contact = Contact.query.get_or_404(contact_id)
    return jsonify(contact_schema.dump(contact))


@app.route('/api/contacts', methods=['POST'])
def create_contact():
    """Create a new contact
    ---
    parameters:
      - in: body
        name: contact
        schema:
          type: object
          required:
            - role
            - name
          properties:
            role:
              type: string
            name:
              type: string
            phone:
              type: string
            email:
              type: string
            on_call:
              type: boolean
    responses:
      201:
        description: Contact created
      400:
        description: Invalid data
    """
    data = request.get_json()

    contact = Contact(
        role=data['role'],
        name=data['name'],
        phone=data.get('phone'),
        email=data.get('email'),
        on_call=data.get('on_call', False)
    )

    db.session.add(contact)
    db.session.commit()

    return jsonify(contact_schema.dump(contact)), 201


# Statistics endpoints
@app.route('/api/statistics/occupancy', methods=['GET'])
def get_occupancy_stats():
    """Get room occupancy statistics
    ---
    parameters:
      - name: start_date
        in: query
        type: string
        required: false
        description: Start date (YYYY-MM-DD), defaults to 30 days ago
      - name: end_date
        in: query
        type: string
        required: false
        description: End date (YYYY-MM-DD), defaults to today
    responses:
      200:
        description: Occupancy statistics
    """
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        start_date = datetime.strptime(start_date_str,
                                       '%Y-%m-%d').date() if start_date_str else date.today() - timedelta(days=30)
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Get total rooms
    total_rooms = Room.query.filter_by(is_active=True).count()

    # Get confirmed bookings in date range
    confirmed_bookings = Booking.query.filter(
        Booking.status.in_(['confirmed', 'checked_in']),
        Booking.check_in <= end_date,
        Booking.check_out >= start_date
    ).all()

    # Calculate occupancy rate
    total_booked_nights = sum(
        (min(booking.check_out, end_date) - max(booking.check_in, start_date)).days
        for booking in confirmed_bookings
    )

    total_possible_nights = total_rooms * (end_date - start_date).days

    occupancy_rate = (total_booked_nights / total_possible_nights * 100) if total_possible_nights > 0 else 0

    # Additional statistics
    revenue = sum(booking.total_amount for booking in confirmed_bookings)
    avg_stay_length = total_booked_nights / len(confirmed_bookings) if confirmed_bookings else 0

    stats = {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'total_rooms': total_rooms,
        'total_bookings': len(confirmed_bookings),
        'total_booked_nights': total_booked_nights,
        'occupancy_rate': round(occupancy_rate, 2),
        'total_revenue': revenue,
        'average_stay_length': round(avg_stay_length, 2)
    }

    return jsonify(stats)


@app.route('/api/statistics/yearly-summary', methods=['GET'])
def get_yearly_summary():
    """Get yearly occupancy summary (GitHub contributions style)
    ---
    parameters:
      - name: year
        in: query
        type: integer
        required: false
        description: Year (defaults to current year)
    responses:
      200:
        description: Yearly summary data
    """
    year = request.args.get('year', datetime.now().year, type=int)

    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Get all bookings for the year
    bookings = Booking.query.filter(
        Booking.check_in <= end_date,
        Booking.check_out >= start_date,
        Booking.status.in_(['confirmed', 'checked_in'])
    ).all()

    # Calculate daily occupancy
    daily_occupancy = {}
    current_date = start_date
    while current_date <= end_date:
        daily_bookings = [
            b for b in bookings
            if b.check_in <= current_date and b.check_out > current_date
        ]
        daily_occupancy[current_date.isoformat()] = len(daily_bookings)
        current_date += timedelta(days=1)

    return jsonify({
        'year': year,
        'daily_occupancy': daily_occupancy,
        'total_bookings': len(bookings),
        'total_revenue': sum(booking.total_amount for booking in bookings)
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)