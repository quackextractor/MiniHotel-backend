from app import app
from flasgger import Swagger

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

template = {
    "swagger": "2.0",
    "info": {
        "title": "Minihotel Management API",
        "description": "REST API for hotel management system based on Minihotel Megadocs - Enhanced Version",
        "version": "2.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@minihotel.com"
        }
    },
    "basePath": "/api",
    "schemes": ["http", "https"]
}

Swagger(app, config=swagger_config, template=template)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)