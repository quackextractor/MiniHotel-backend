from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
from collections import defaultdict
from database import db, Room, Booking, AuditLog
from schemas import booking_schema, audit_logs_schema
from utils import token_required

report_bp = Blueprint('report', __name__, url_prefix='/api')

@report_bp.route('/audit-logs', methods=['GET'])
@token_required
def get_audit_logs(current_user):
    """Get audit logs"""
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return jsonify(audit_logs_schema.dump(logs))


@report_bp.route('/availability', methods=['GET'])
@token_required
def get_availability(current_user):
    """Get room availability for a date range"""
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


@report_bp.route('/calendar/weekly', methods=['GET'])
@token_required
def get_weekly_calendar(current_user):
    """Get weekly calendar view"""
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


@report_bp.route('/calendar/monthly', methods=['GET'])
@token_required
def get_monthly_calendar(current_user):
    """Get monthly calendar view"""
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


@report_bp.route('/statistics/occupancy', methods=['GET'])
@token_required
def get_occupancy_stats(current_user):
    """Get room occupancy statistics"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    try:
        start_date = datetime.strptime(start_date_str,
                                       '%Y-%m-%d').date() if start_date_str else date.today() - timedelta(days=30)
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else date.today()
    except (ValueError, TypeError):
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

    # Calculate daily occupancy
    daily_occupancy = []
    
    current_date = start_date
    while current_date <= end_date:
        # Count occupied rooms for this date
        occupied_count = 0
        for booking in confirmed_bookings:
            if booking.check_in <= current_date < booking.check_out:
                occupied_count += 1
        
        daily_rate = (occupied_count / total_rooms * 100) if total_rooms > 0 else 0
        daily_occupancy.append({
            'date': current_date.isoformat(),
            'occupancy_rate': round(daily_rate, 2),
            'occupied_rooms': occupied_count
        })
        current_date += timedelta(days=1)

    # Unique guests
    unique_guests = len(set(b.guest_id for b in confirmed_bookings))

    # Calculate Room Type Performance
    room_type_stats = defaultdict(int)
    for booking in confirmed_bookings:
        if booking.room:
            room_type_stats[booking.room.room_type] += 1

    room_type_performance = [
        {'room_type': k, 'booking_count': v} 
        for k, v in room_type_stats.items()
    ]

    stats = {
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'total_rooms': total_rooms,
        'total_bookings': len(confirmed_bookings),
        'total_booked_nights': total_booked_nights,
        'occupancy_rate': round(occupancy_rate, 2),
        'average_occupancy_rate': round(occupancy_rate, 2),
        'total_revenue': revenue,
        'average_stay_length': round(avg_stay_length, 2),
        'unique_guests': unique_guests,
        'daily_occupancy': daily_occupancy,
        'room_type_performance': room_type_performance
    }

    return jsonify(stats)


@report_bp.route('/statistics/yearly-summary', methods=['GET'])
@token_required
def get_yearly_summary(current_user):
    """Get yearly occupancy summary"""
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
