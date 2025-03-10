from flask import request, jsonify, current_app
from flask_login import login_required
from . import transactions_bp
from ..models import BankSettings
from ..utils.crypto import generate_jwks
from ..utils.transaction_handler import process_incoming_transaction
import base64
import json

@transactions_bp.route('/b2b', methods=['POST'])
def b2b_transaction():
    """Endpoint for receiving transactions from other banks."""
    try:
        data = request.get_json()
        if not data or 'jwt' not in data:
            return jsonify({'error': 'Invalid request format'}), 400
        
        jwt_token = data['jwt']
        
        # Process the incoming transaction
        response, status_code = process_incoming_transaction(jwt_token)
        
        return jsonify(response), status_code
    except Exception as e:
        current_app.logger.error(f"Error processing B2B transaction: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@transactions_bp.route('/jwks', methods=['GET'])
def jwks():
    """JWKS endpoint for exposing the bank's public key."""
    try:
        # Get the bank settings
        bank_settings = BankSettings.query.first()
        if not bank_settings or not bank_settings.public_key:
            return jsonify({'error': 'Bank not properly configured with keys'}), 500
        
        # Generate JWKS from the public key
        jwks_data = generate_jwks(bank_settings.public_key)
        
        return jsonify(jwks_data)
    except Exception as e:
        current_app.logger.error(f"Error serving JWKS: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
