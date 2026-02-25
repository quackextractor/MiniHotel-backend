from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db, Room, RoomGroup, SeasonalRate, Booking
from schemas import room_schema, rooms_schema, room_group_schema, room_groups_schema, seasonal_rate_schema, seasonal_rates_schema
from utils import token_required

room_bp = Blueprint('room', __name__)

# Room endpoints
@room_bp.route('/api/rooms', methods=['GET'])
@token_required
def get_rooms(current_user):
    """Get all rooms
    ---
    parameters:
      - name: active
        in: query
        type: boolean
        required: false
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


@room_bp.route('/api/rooms/<int:room_id>', methods=['GET'])
@token_required
def get_room(current_user, room_id):
    """Get room by ID"""
    room = Room.query.get_or_404(room_id)
    return jsonify(room_schema.dump(room))


@room_bp.route('/api/rooms', methods=['POST'])
@token_required
def create_room(current_user):
    """Create a new room"""
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
        is_active=data.get('is_active', True),
        amenities=data.get('amenities', '')
    )

    db.session.add(room)
    db.session.commit()

    return jsonify(room_schema.dump(room)), 201


@room_bp.route('/api/rooms/<int:room_id>', methods=['PUT'])
@token_required
def update_room(current_user, room_id):
    """Update an existing room"""
    room = Room.query.get_or_404(room_id)
    data = request.get_json()

    if 'room_number' in data and data['room_number'] != room.room_number:
        if Room.query.filter_by(room_number=data['room_number']).first():
            return jsonify({'error': 'Room number already exists'}), 400
        room.room_number = data['room_number']
        
    if 'room_type' in data:
        room.room_type = data['room_type']
    if 'description' in data:
        room.description = data['description']
    if 'capacity' in data:
        room.capacity = data['capacity']
    if 'base_rate' in data:
        room.base_rate = data['base_rate']
    if 'group_id' in data:
        room.group_id = data['group_id']
    if 'is_active' in data:
        room.is_active = data['is_active']
    if 'amenities' in data:
        room.amenities = data['amenities']

    db.session.commit()
    return jsonify(room_schema.dump(room))


@room_bp.route('/api/rooms/<int:room_id>', methods=['DELETE'])
@token_required
def delete_room(current_user, room_id):
    """Delete a room"""
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return jsonify({'message': 'Room deleted successfully'})



# Room Group endpoints
@room_bp.route('/api/room-groups', methods=['GET'])
@token_required
def get_room_groups(current_user):
    """Get all room groups in tree structure"""
    groups = RoomGroup.query.filter_by(parent_group_id=None).all()
    return jsonify(room_groups_schema.dump(groups))


@room_bp.route('/api/room-groups', methods=['POST'])
@token_required
def create_room_group(current_user):
    """Create a new room group"""
    data = request.get_json()

    group = RoomGroup(
        name=data['name'],
        description=data.get('description'),
        parent_group_id=data.get('parent_group_id')
    )

    db.session.add(group)
    db.session.commit()

    return jsonify(room_group_schema.dump(group)), 201


@room_bp.route('/api/room-groups/<int:group_id>', methods=['PUT'])
@token_required
def update_room_group(current_user, group_id):
    """Update an existing room group"""
    group = RoomGroup.query.get_or_404(group_id)
    data = request.get_json()

    if 'name' in data:
        group.name = data['name']
    if 'description' in data:
        group.description = data['description']
    if 'parent_group_id' in data:
        group.parent_group_id = data['parent_group_id']

    db.session.commit()
    return jsonify(room_group_schema.dump(group))


@room_bp.route('/api/room-groups/<int:group_id>', methods=['DELETE'])
@token_required
def delete_room_group(current_user, group_id):
    """Delete a room group"""
    group = RoomGroup.query.get_or_404(group_id)
    db.session.delete(group)
    db.session.commit()
    return jsonify({'message': 'Room group deleted successfully'})




# Seasonal Rates endpoints
@room_bp.route('/api/seasonal-rates', methods=['GET'])
@token_required
def get_seasonal_rates(current_user):
    """Get all seasonal rates"""
    rates = SeasonalRate.query.all()
    return jsonify(seasonal_rates_schema.dump(rates))


@room_bp.route('/api/seasonal-rates', methods=['POST'])
@token_required
def create_seasonal_rate(current_user):
    """Create a new seasonal rate"""
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


@room_bp.route('/api/seasonal-rates/<int:rate_id>', methods=['PUT'])
@token_required
def update_seasonal_rate(current_user, rate_id):
    """Update an existing seasonal rate"""
    rate = SeasonalRate.query.get_or_404(rate_id)
    data = request.get_json()

    if 'name' in data:
        rate.name = data['name']
    if 'start_date' in data:
        rate.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in data:
        rate.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    if 'rate_multiplier' in data:
        rate.rate_multiplier = data['rate_multiplier']
    if 'room_type' in data:
        rate.room_type = data['room_type']
    if 'room_group_id' in data:
        rate.room_group_id = data['room_group_id']

    db.session.commit()
    return jsonify(seasonal_rate_schema.dump(rate))


@room_bp.route('/api/seasonal-rates/<int:rate_id>', methods=['DELETE'])
@token_required
def delete_seasonal_rate(current_user, rate_id):
    """Delete a seasonal rate"""
    rate = SeasonalRate.query.get_or_404(rate_id)
    db.session.delete(rate)
    db.session.commit()
    return jsonify({'message': 'Rate deleted successfully'})
