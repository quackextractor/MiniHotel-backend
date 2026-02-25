from datetime import datetime, timedelta
from flask import jsonify
from database import db, Room, Booking, Guest, BookingService as BookingServiceModel, SeasonalRate, Service
from schemas import booking_schema

class BookingService:
    @staticmethod
    def calculate_rate(room_id, check_in_date, check_out_date, number_of_guests, service_ids=None):
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

        # Calculate services cost
        services_total = 0
        if service_ids:
            services = Service.query.filter(Service.id.in_(service_ids)).all()
            for service in services:
                services_total += service.price

        total_amount = ((base_amount + seasonal_adjustment) * capacity_multiplier) + services_total

        return {
            'base_amount': base_amount,
            'seasonal_adjustment': seasonal_adjustment,
            'capacity_multiplier': capacity_multiplier,
            'services_total': services_total,
            'total_amount': round(total_amount, 2),
            'total_nights': total_nights
        }

    @staticmethod
    def create_booking(data):
        check_in_date = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        check_out_date = datetime.strptime(data['check_out'], '%Y-%m-%d').date()

        if check_in_date >= check_out_date:
            raise ValueError('Check-out date must be after check-in date')

        # Check room availability (skip for draft status)
        status = data.get('status', 'confirmed')
        if status not in ['draft', 'tentative']:
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
        db.session.flush() # Get ID

        # Add services if provided
        if 'services' in data and data['services']:
            for svc_item in data['services']:
                # Handle both list of IDs and list of objects
                svc_id = svc_item['service_id'] if isinstance(svc_item, dict) else svc_item
                quantity = svc_item.get('quantity', 1) if isinstance(svc_item, dict) else 1
                svc_date = svc_item.get('date') if isinstance(svc_item, dict) else None
                
                # Default to check-in date if not specified
                if not svc_date:
                    svc_date = booking.check_in
                else:
                    try:
                        svc_date = datetime.strptime(svc_date, '%Y-%m-%d').date()
                    except:
                        svc_date = booking.check_in

                booking_service = BookingServiceModel(
                    booking_id=booking.id,
                    service_id=svc_id,
                    quantity=quantity,
                    date=svc_date
                )
                db.session.add(booking_service)

        db.session.commit()

        return booking
