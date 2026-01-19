from __init__ import create_app
from flask import jsonify, request
from importer import import_all_data
from utils import token_required

app = create_app()

@app.cli.command("import-data")
def cli_import_data():
    """Import sample data from JSON files."""
    import_all_data()

@app.route('/api/import-data', methods=['POST'])
@token_required
def api_import_data(current_user):
    """Import sample data via API
    ---
    responses:
      200:
        description: Data import initiated
      500:
        description: Import failed
    """
    success = import_all_data()
    if success:
        return jsonify({'message': 'Data imported successfully'}), 200
    else:
        return jsonify({'error': 'Data import failed'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint
    ---
    responses:
      200:
        description: API is running
    """
    from datetime import datetime
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)