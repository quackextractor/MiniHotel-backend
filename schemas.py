from flask_marshmallow import Marshmallow

from database import Room, Guest, Booking, Event, Housekeeping, Maintenance, Contact, RoomGroup, SeasonalRate, Service, \
    BookingService, User, AuditLog

ma = Marshmallow()

class RoomGroupSchema(ma.Schema):
    class Meta:
        model = RoomGroup
        load_instance = True

    id = ma.Int()
    name = ma.Str()
    description = ma.Str()
    parent_group_id = ma.Int()
    children = ma.Nested(lambda: RoomGroupSchema(many=True))
    rooms = ma.Nested(lambda: RoomSchema(many=True))

class SeasonalRateSchema(ma.Schema):
    class Meta:
        model = SeasonalRate
        load_instance = True

    id = ma.Int()
    name = ma.Str()
    start_date = ma.Date()
    end_date = ma.Date()
    rate_multiplier = ma.Float()
    room_type = ma.Str()
    room_group_id = ma.Int()

class ServiceSchema(ma.Schema):
    class Meta:
        model = Service
        load_instance = True

    id = ma.Int()
    name = ma.Str()
    description = ma.Str()
    price = ma.Float()
    is_active = ma.Bool()

class BookingServiceSchema(ma.Schema):
    class Meta:
        model = BookingService
        load_instance = True

    id = ma.Int()
    booking_id = ma.Int()
    service_id = ma.Int()
    quantity = ma.Int()
    date = ma.Date()
    service = ma.Nested(ServiceSchema)

class RoomSchema(ma.Schema):
    class Meta:
        model = Room
        include_fk = True
        load_instance = True

    id = ma.Int()
    room_number = ma.Str()
    room_type = ma.Str()
    description = ma.Str()
    capacity = ma.Int()
    base_rate = ma.Float()
    group_id = ma.Int()
    is_active = ma.Bool()
    group = ma.Nested(RoomGroupSchema)

class GuestSchema(ma.Schema):
    class Meta:
        model = Guest
        load_instance = True

    id = ma.Int()
    first_name = ma.Str()
    last_name = ma.Str()
    email = ma.Str()
    phone = ma.Str()
    address = ma.Str()

class BookingSchema(ma.Schema):
    class Meta:
        model = Booking
        include_fk = True
        load_instance = True

    id = ma.Int()
    booking_id = ma.Str()
    guest_id = ma.Int()
    room_id = ma.Int()
    check_in = ma.Date()
    check_out = ma.Date()
    number_of_guests = ma.Int()
    total_amount = ma.Float()
    status = ma.Str()
    payment_status = ma.Str()
    payment_method = ma.Str()
    notes = ma.Str()
    assigned_to = ma.Str()
    created_at = ma.DateTime()
    recreational_fee = ma.Float()
    consumed_amount = ma.Float()

    guest = ma.Nested(GuestSchema)
    room = ma.Nested(RoomSchema)
    services = ma.Nested(BookingServiceSchema(many=True))

class EventSchema(ma.Schema):
    class Meta:
        model = Event
        load_instance = True

    id = ma.Int()
    event_id = ma.Str()
    name = ma.Str()
    event_date = ma.Date()
    space = ma.Str()
    expected_guests = ma.Int()
    status = ma.Str()
    contact_email = ma.Str()
    contact_phone = ma.Str()
    notes = ma.Str()

class HousekeepingSchema(ma.Schema):
    class Meta:
        model = Housekeeping
        include_fk = True
        load_instance = True

    id = ma.Int()
    room_id = ma.Int()
    status = ma.Str()
    last_cleaned = ma.Date()
    cleaner = ma.Str()
    notes = ma.Str()
    updated_at = ma.DateTime()

    room = ma.Nested(RoomSchema)

class MaintenanceSchema(ma.Schema):
    class Meta:
        model = Maintenance
        load_instance = True

    id = ma.Int()
    ticket_id = ma.Str()
    area = ma.Str()
    issue = ma.Str()
    reported_date = ma.Date()
    priority = ma.Str()
    status = ma.Str()
    assigned_to = ma.Str()
    notes = ma.Str()

class ContactSchema(ma.Schema):
    class Meta:
        model = Contact
        load_instance = True

    id = ma.Int()
    role = ma.Str()
    name = ma.Str()
    phone = ma.Str()
    email = ma.Str()
    email = ma.Str()
    on_call = ma.Bool()

class UserSchema(ma.Schema):
    class Meta:
        model = User
        load_instance = True

    id = ma.Int()
    username = ma.Str()
    created_at = ma.DateTime()

class AuditLogSchema(ma.Schema):
    class Meta:
        model = AuditLog
        load_instance = True

    id = ma.Int()
    user_id = ma.Int()
    action = ma.Str()
    details = ma.Str()
    timestamp = ma.DateTime()
    ip_address = ma.Str()
    user = ma.Nested(UserSchema)


# Initialize schemas
room_schema = RoomSchema()
rooms_schema = RoomSchema(many=True)
guest_schema = GuestSchema()
guests_schema = GuestSchema(many=True)
booking_schema = BookingSchema()
bookings_schema = BookingSchema(many=True)
event_schema = EventSchema()
events_schema = EventSchema(many=True)
housekeeping_schema = HousekeepingSchema()
housekeepings_schema = HousekeepingSchema(many=True)
maintenance_schema = MaintenanceSchema()
maintenances_schema = MaintenanceSchema(many=True)
contact_schema = ContactSchema()
contacts_schema = ContactSchema(many=True)
room_group_schema = RoomGroupSchema()
room_groups_schema = RoomGroupSchema(many=True)
seasonal_rate_schema = SeasonalRateSchema()
seasonal_rates_schema = SeasonalRateSchema(many=True)
service_schema = ServiceSchema()
services_schema = ServiceSchema(many=True)
booking_service_schema = BookingServiceSchema()
booking_services_schema = BookingServiceSchema(many=True)
user_schema = UserSchema()
users_schema = UserSchema(many=True)
audit_log_schema = AuditLogSchema()
audit_logs_schema = AuditLogSchema(many=True)
