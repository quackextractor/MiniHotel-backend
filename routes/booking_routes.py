from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db, Booking, Guest, BookingService as BookingServiceModel, Service
from schemas import booking_schema, bookings_schema, booking_service_schema
from utils import token_required
from services.booking_service import BookingService

booking_bp = Blueprint('booking', __name__, url_prefix='/api/bookings')

@booking_bp.route('', methods=['GET'])
@token_required
def get_bookings(current_user):
    """Get all bookings with optional filters and pagination
    ---
    parameters:
      - name: status
        in: query
        type: string
        required: false
      - name: date
        in: query
        type: string
        required: false
      - name: guest_name
        in: query
        type: string
        required: false
      - name: room_id
        in: query
        type: integer
        required: false
      - name: page
        in: query
        type: integer
        default: 1
      - name: per_page
        in: query
        type: integer
        default: 20
    responses:
      200:
        description: List of bookings
    """
    status = request.args.get('status')
    date_str = request.args.get('date')
    guest_name = request.args.get('guest_name')
    room_id = request.args.get('room_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

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

    # Implement pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': bookings_schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@booking_bp.route('/<int:booking_id>', methods=['GET'])
@token_required
def get_booking(current_user, booking_id):
    """Get booking by ID"""
    booking = Booking.query.get_or_404(booking_id)
    return jsonify(booking_schema.dump(booking))


@booking_bp.route('/calculate-rate', methods=['POST'])
@token_required
def calculate_booking_rate(current_user):
    """Calculate booking rate"""
    data = request.get_json()
    try:
        check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        
        result = BookingService.calculate_rate(
            room_id=data['room_id'],
            check_in_date=check_in,
            check_out_date=check_out,
            number_of_guests=data.get('number_of_guests', 1)
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@booking_bp.route('', methods=['POST'])
@token_required
def create_booking(current_user):
    """Create a new booking"""
    data = request.get_json()
    try:
        booking = BookingService.create_booking(data)
        return jsonify(booking_schema.dump(booking)), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@booking_bp.route('/<int:booking_id>/status', methods=['PATCH'])
@token_required
def update_booking_status(current_user, booking_id):
    """Update booking status"""
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json()

    if 'status' in data:
        booking.status = data['status']

    if 'payment_status' in data:
        booking.payment_status = data['payment_status']

    db.session.commit()

    return jsonify(booking_schema.dump(booking))


@booking_bp.route('/<int:booking_id>', methods=['DELETE'])
@token_required
def delete_booking(current_user, booking_id):
    """Delete a booking"""
    booking = Booking.query.get_or_404(booking_id)

    # Clean up related records
    BookingServiceModel.query.filter_by(booking_id=booking.id).delete()
    
    db.session.delete(booking)
    db.session.commit()

    return jsonify({'message': 'Booking deleted successfully'})


@booking_bp.route('/<int:booking_id>/services', methods=['POST'])
@token_required
def add_booking_service(current_user, booking_id):
    """Add a service to a booking"""
    data = request.get_json()

    # Check if booking exists
    booking = Booking.query.get_or_404(booking_id)
    # Check if service exists
    service = Service.query.get_or_404(data['service_id'])

    booking_service = BookingServiceModel(
        booking_id=booking_id,
        service_id=data['service_id'],
        quantity=data.get('quantity', 1),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date()
    )

    db.session.add(booking_service)
    db.session.commit()

    return jsonify(booking_service_schema.dump(booking_service)), 201
