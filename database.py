from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    space = db.Column(db.String(100))
    status = db.Column(db.String(20), default='scheduled')
    expected_guests = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Event {self.name}>'


class RoomGroup(db.Model):
    __tablename__ = 'room_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_group_id = db.Column(db.Integer, db.ForeignKey('room_groups.id'))

    children = db.relationship('RoomGroup', backref=db.backref('parent', remote_side=[id]))
    rooms = db.relationship('Room', backref='group')


class SeasonalRate(db.Model):
    __tablename__ = 'seasonal_rates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    rate_multiplier = db.Column(db.Float, nullable=False, default=1.0)  # 1.1 = 10% increase
    room_type = db.Column(db.String(50))  # Specific room type or null for all
    room_group_id = db.Column(db.Integer, db.ForeignKey('room_groups.id'))

    room_group = db.relationship('RoomGroup', backref='seasonal_rates')


class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)


class BookingService(db.Model):
    __tablename__ = 'booking_services'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    date = db.Column(db.Date, nullable=False)

    booking = db.relationship('Booking', backref='services')
    service = db.relationship('Service', backref='bookings')


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    capacity = db.Column(db.Integer, nullable=False)
    base_rate = db.Column(db.Float, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('room_groups.id'))
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Room {self.room_number}>'


class Guest(db.Model):
    __tablename__ = 'guests'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)

    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True, nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    number_of_guests = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False,
                       default='confirmed')  # draft, confirmed, tentative, pending_payment, checked_in, checked_out, cancelled, no_show
    payment_status = db.Column(db.String(20), nullable=False, default='not_paid')  # paid, not_paid, pending, refunded
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    assigned_to = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.now())

    # New fields for enhanced functionality
    recreational_fee = db.Column(db.Float, default=0.0)
    consumed_amount = db.Column(db.Float, default=0.0)  # For restaurant/consumption tracking

    guest = db.relationship('Guest', backref='bookings')
    room = db.relationship('Room', backref='bookings')

    def __repr__(self):
        return f'<Booking {self.booking_id}>'




class Housekeeping(db.Model):
    __tablename__ = 'housekeeping'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    status = db.Column(db.String(30),
                       nullable=False)  # clean, dirty, inspection_needed, out_of_service, deep_clean_required
    last_cleaned = db.Column(db.Date)
    cleaner = db.Column(db.String(100))
    notes = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=db.func.now())

    room = db.relationship('Room', backref='housekeeping_records')

    def __repr__(self):
        return f'<Housekeeping Room {self.room.room_number}>'


class Maintenance(db.Model):
    __tablename__ = 'maintenance'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)
    area = db.Column(db.String(100), nullable=False)
    issue = db.Column(db.Text, nullable=False)
    reported_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(20), nullable=False)  # high, medium, low
    status = db.Column(db.String(20), nullable=False)  # new, in_progress, on_hold, completed, cancelled
    assigned_to = db.Column(db.String(100))
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Maintenance {self.ticket_id}>'


class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    on_call = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Contact {self.name} - {self.role}>'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<User {self.username}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    ip_address = db.Column(db.String(50))

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'

class ExchangeRate(db.Model):
    __tablename__ = 'exchange_rates'

    id = db.Column(db.Integer, primary_key=True)
    currency_code = db.Column(db.String(10), unique=True, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    last_updated = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    is_tracked = db.Column(db.Boolean, default=True)  # Set to True for currencies we want to actively fetch

    def __repr__(self):
        return f'<ExchangeRate {self.currency_code}: {self.rate}>'
