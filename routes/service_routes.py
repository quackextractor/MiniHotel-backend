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
