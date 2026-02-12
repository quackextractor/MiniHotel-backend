from flask import Blueprint, request, jsonify
from datetime import datetime, date
from database import db, Housekeeping, Maintenance, Contact
from schemas import housekeeping_schema, housekeepings_schema, maintenance_schema, maintenances_schema, contact_schema, contacts_schema
from utils import token_required

operations_bp = Blueprint('operations', __name__, url_prefix='/api')

# Housekeeping endpoints
@operations_bp.route('/housekeeping', methods=['GET'])
@token_required
def get_housekeeping(current_user):
    """Get all housekeeping records"""
    room_id = request.args.get('room_id')
    status = request.args.get('status')

    query = Housekeeping.query

    if room_id:
        query = query.filter_by(room_id=room_id)

    if status:
        query = query.filter_by(status=status)

    records = query.all()
    return jsonify(housekeepings_schema.dump(records))


@operations_bp.route('/housekeeping/<int:record_id>', methods=['GET'])
@token_required
def get_housekeeping_record(current_user, record_id):
    """Get housekeeping record by ID"""
    record = Housekeeping.query.get_or_404(record_id)
    return jsonify(housekeeping_schema.dump(record))


@operations_bp.route('/housekeeping', methods=['POST'])
@token_required
def create_housekeeping(current_user):
    """Create a new housekeeping record"""
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


@operations_bp.route('/housekeeping/<int:record_id>', methods=['PUT'])
@token_required
def update_housekeeping(current_user, record_id):
    """Update a housekeeping record"""
    record = Housekeeping.query.get_or_404(record_id)
    data = request.get_json()

    if 'status' in data:
        record.status = data['status']
    
    if 'cleaner' in data:
        record.cleaner = data['cleaner']
    
    if 'notes' in data:
        record.notes = data['notes']
        
    if 'last_cleaned' in data:
         record.last_cleaned = datetime.strptime(data['last_cleaned'], '%Y-%m-%d').date()

    db.session.commit()
    return jsonify(housekeeping_schema.dump(record))


# Maintenance endpoints
@operations_bp.route('/maintenance', methods=['GET'])
@token_required
def get_maintenance(current_user):
    """Get all maintenance tickets"""
    status = request.args.get('status')
    priority = request.args.get('priority')

    query = Maintenance.query

    if status:
        query = query.filter_by(status=status)

    if priority:
        query = query.filter_by(priority=priority)

    tickets = query.all()
    return jsonify(maintenances_schema.dump(tickets))


@operations_bp.route('/maintenance/<int:ticket_id>', methods=['GET'])
@token_required
def get_maintenance_ticket(current_user, ticket_id):
    """Get maintenance ticket by ID"""
    ticket = Maintenance.query.get_or_404(ticket_id)
    return jsonify(maintenance_schema.dump(ticket))


@operations_bp.route('/maintenance', methods=['POST'])
@token_required
def create_maintenance(current_user):
    """Create a new maintenance ticket"""
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
@operations_bp.route('/contacts', methods=['GET'])
@token_required
def get_contacts(current_user):
    """Get all contacts"""
    role = request.args.get('role')
    on_call = request.args.get('on_call')

    query = Contact.query

    if role:
        query = query.filter_by(role=role)

    if on_call:
        query = query.filter_by(on_call=on_call.lower() == 'true')

    contacts = query.all()
    return jsonify(contacts_schema.dump(contacts))


@operations_bp.route('/contacts/<int:contact_id>', methods=['GET'])
@token_required
def get_contact(current_user, contact_id):
    """Get contact by ID"""
    contact = Contact.query.get_or_404(contact_id)
    return jsonify(contact_schema.dump(contact))


@operations_bp.route('/contacts', methods=['POST'])
@token_required
def create_contact(current_user):
    """Create a new contact"""
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
