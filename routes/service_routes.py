from flask import Blueprint, request, jsonify
from database import db, Service
from schemas import service_schema, services_schema
from utils import token_required

service_bp = Blueprint('service', __name__, url_prefix='/api/services')

@service_bp.route('', methods=['GET'])
@token_required
def get_services(current_user):
    """Get all active services
    ---
    responses:
      200:
        description: List of services
    """
    services = Service.query.filter_by(is_active=True).all()
    return jsonify(services_schema.dump(services))


@service_bp.route('', methods=['POST'])
@token_required
def create_service(current_user):
    """Create a new service
    ---
    responses:
      201:
        description: Service created
      400:
        description: Invalid data
    """
    data = request.get_json()

    service = Service(
        name=data['name'],
        description=data.get('description'),
        price=data['price']
    )

    db.session.add(service)
    db.session.commit()

    return jsonify(service_schema.dump(service)), 201


@service_bp.route('/<int:service_id>', methods=['PUT'])
@token_required
def update_service(current_user, service_id):
    """Update a service"""
    service = Service.query.get_or_404(service_id)
    data = request.get_json()

    if 'name' in data:
        service.name = data['name']
    if 'description' in data:
        service.description = data['description']
    if 'price' in data:
        service.price = data['price']
    if 'is_active' in data:
        service.is_active = data['is_active']

    db.session.commit()
    return jsonify(service_schema.dump(service))


@service_bp.route('/<int:service_id>', methods=['DELETE'])
@token_required
def delete_service(current_user, service_id):
    """Soft delete a service"""
    service = Service.query.get_or_404(service_id)
    service.is_active = False
    db.session.commit()
    return jsonify({'message': 'Service deleted successfully'})
