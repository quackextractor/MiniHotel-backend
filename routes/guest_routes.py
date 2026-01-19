from flask import Blueprint, request, jsonify
from database import db, Guest, Booking
from schemas import guest_schema, guests_schema, bookings_schema
from utils import token_required

guest_bp = Blueprint('guest', __name__, url_prefix='/api/guests')

@guest_bp.route('', methods=['GET'])
@token_required
def get_guests(current_user):
    """Get all guests
    ---
    parameters:
      - name: search
        in: query
        type: string
        required: false
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


@guest_bp.route('/<int:guest_id>', methods=['GET'])
@token_required
def get_guest(current_user, guest_id):
    """Get guest by ID"""
    guest = Guest.query.get_or_404(guest_id)
    return jsonify(guest_schema.dump(guest))


@guest_bp.route('', methods=['POST'])
@token_required
def create_guest(current_user):
    """Create a new guest"""
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


@guest_bp.route('/search', methods=['GET'])
@token_required
def search_guests(current_user):
    """Enhanced guest search by name, email, or phone"""
    query_str = request.args.get('q', '')

    if not query_str:
        return jsonify([])

    guests = Guest.query.filter(
        (Guest.first_name.ilike(f'%{query_str}%')) |
        (Guest.last_name.ilike(f'%{query_str}%')) |
        (Guest.email.ilike(f'%{query_str}%')) |
        (Guest.phone.ilike(f'%{query_str}%'))
    ).all()

    return jsonify(guests_schema.dump(guests))


@guest_bp.route('/<int:guest_id>/bookings', methods=['GET'])
@token_required
def get_guest_bookings(current_user, guest_id):
    """Get booking history for a specific guest"""
    guest = Guest.query.get_or_404(guest_id)
    bookings = Booking.query.filter_by(guest_id=guest_id).order_by(Booking.created_at.desc()).all()
    return jsonify(bookings_schema.dump(bookings))
