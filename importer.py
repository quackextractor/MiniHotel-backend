import json
from datetime import datetime
from pathlib import Path
from database import db, Room, Guest, Service, SeasonalRate, Contact, Booking

def import_all_data():
    """Helper function to import all data"""
    data_dir = Path("example_data")
    if not data_dir.exists():
        print("Error: example_data directory not found")
        return False

    try:
        # Import Rooms
        try:
            with open(data_dir / "rooms.json") as f:
                rooms_data = json.load(f)
                for item in rooms_data:
                    if not Room.query.filter_by(room_number=item['room_number']).first():
                        room = Room(**item)
                        db.session.add(room)
                db.session.commit()
                print("Rooms imported.")
        except Exception as e:
            print(f"Error importing rooms: {e}")

        # Import Guests
        try:
            with open(data_dir / "guests.json") as f:
                guests_data = json.load(f)
                for item in guests_data:
                    if not Guest.query.filter_by(email=item['email']).first():
                        guest = Guest(**item)
                        db.session.add(guest)
                db.session.commit()
                print("Guests imported.")
        except Exception as e:
            print(f"Error importing guests: {e}")

        # Import Services
        try:
            with open(data_dir / "services.json") as f:
                services_data = json.load(f)
                for item in services_data:
                    if not Service.query.filter_by(name=item['name']).first():
                        service = Service(**item)
                        db.session.add(service)
                db.session.commit()
                print("Services imported.")
        except Exception as e:
            print(f"Error importing services: {e}")
        
        # Import Seasonal Rates
        try:
            with open(data_dir / "seasonal_rates.json") as f:
                rates_data = json.load(f)
                for item in rates_data:
                    if not SeasonalRate.query.filter_by(name=item['name']).first():
                        # Parse dates
                        item['start_date'] = datetime.strptime(item['start_date'], '%Y-%m-%d').date()
                        item['end_date'] = datetime.strptime(item['end_date'], '%Y-%m-%d').date()
                        rate = SeasonalRate(**item)
                        db.session.add(rate)
                db.session.commit()
                print("Seasonal rates imported.")
        except Exception as e:
            print(f"Error importing seasonal rates: {e}")

        # Import Contacts
        try:
            with open(data_dir / "contacts.json") as f:
                contacts_data = json.load(f)
                for item in contacts_data:
                    if not Contact.query.filter_by(name=item['name']).first():
                        contact = Contact(**item)
                        db.session.add(contact)
                db.session.commit()
                print("Contacts imported.")
        except Exception as e:
            print(f"Error importing contacts: {e}")

        # Import Bookings
        try:
            with open(data_dir / "bookings.json") as f:
                bookings_data = json.load(f)
                for item in bookings_data:
                    if not Booking.query.filter_by(booking_id=item['booking_id']).first():
                        # Resolve foreign keys
                        guest = Guest.query.filter_by(email=item.pop('guest_email')).first()
                        room = Room.query.filter_by(room_number=item.pop('room_number')).first()
                        
                        if guest and room:
                            item['guest_id'] = guest.id
                            item['room_id'] = room.id
                            item['check_in'] = datetime.strptime(item['check_in'], '%Y-%m-%d').date()
                            item['check_out'] = datetime.strptime(item['check_out'], '%Y-%m-%d').date()
                            
                            booking = Booking(**item)
                            db.session.add(booking)
                db.session.commit()
                print("Bookings imported.")
        except Exception as e:
            print(f"Error importing bookings: {e}")
            
        return True
    except Exception as e:
        print(f"Import process failed: {e}")
        return False
