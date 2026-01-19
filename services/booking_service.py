from datetime import datetime, timedelta
from flask import jsonify
from database import db, Room, Booking, Guest, BookingService as BookingServiceModel, SeasonalRate
from schemas import booking_schema

class BookingService:
    @staticmethod
    def calculate_rate(room_id, check_in_date, check_out_date, number_of_guests):
        room = Room.query.get_or_404(room_id)
        
        # Calculate base rate
        total_nights = (check_out_date - check_in_date).days
        base_amount = room.base_rate * total_nights

        # Apply seasonal rates if any
        current_date = check_in_date
        seasonal_adjustment = 0

        while current_date < check_out_date:
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

        return {
            'base_amount': base_amount,
            'seasonal_adjustment': seasonal_adjustment,
            'capacity_multiplier': capacity_multiplier,
            'total_amount': round(total_amount, 2),
            'total_nights': total_nights
        }

    @staticmethod
    def create_booking(data):
        # Check room availability (skip for draft status)
        status = data.get('status', 'confirmed')
        if status not in ['draft', 'tentative']:
            check_in_date = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
            check_out_date = datetime.strptime(data['check_out'], '%Y-%m-%d').date()

            conflicting_booking = Booking.query.filter(
                Booking.room_id == data['room_id'],
                Booking.status.in_(['confirmed', 'checked_in', 'pending_payment']),
                Booking.check_in < check_out_date,
                Booking.check_out > check_in_date
            ).first()

            if conflicting_booking:
                raise ValueError('Room not available for the selected dates')

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

        return booking
