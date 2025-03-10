import requests
import json
from flask import current_app
import os
from ..models import BankSettings
from .. import db

def register_with_central_bank():
    """Register the bank with the Central Bank."""
    if current_app.config.get('TEST_MODE'):
        # Mock response in test mode
        return {
            'success': True,
            'bank_prefix': current_app.config.get('BANK_PREFIX'),
            'api_key': 'test_api_key'
        }
    
    try:
        # Get the bank settings
        bank_settings = BankSettings.query.first()
        if not bank_settings:
            bank_settings = BankSettings(
                bank_name=os.environ.get('BANK_NAME', 'My Bank'),
                transaction_url=os.environ.get('TRANSACTION_URL', 'http://localhost:5000/transactions/b2b'),
                jwks_url=os.environ.get('JWKS_URL', 'http://localhost:5000/transactions/jwks')
            )
        
        # Prepare the registration data
        registration_data = {
            'bank_name': bank_settings.bank_name,
            'transaction_url': bank_settings.transaction_url,
            'jwks_url': bank_settings.jwks_url,
            'owner_info': os.environ.get('OWNER_INFO', 'Bank Owner')
        }
        
        # Send the registration request to the Central Bank
        response = requests.post(
            f"{current_app.config.get('CENTRAL_BANK_URL')}/register",
            json=registration_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Update the bank settings
            bank_settings.bank_prefix = data.get('bank_prefix')
            bank_settings.api_key = data.get('api_key')
            bank_settings.central_bank_url = current_app.config.get('CENTRAL_BANK_URL')
            
            db.session.add(bank_settings)
            db.session.commit()
            
            return {
                'success': True,
                'bank_prefix': data.get('bank_prefix'),
                'api_key': data.get('api_key')
            }
        else:
            return {
                'success': False,
                'error': f"Failed to register with Central Bank: {response.text}"
            }
    except Exception as e:
        current_app.logger.error(f"Error registering with Central Bank: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_bank_details(bank_prefix):
    """Get bank details from the Central Bank by bank prefix."""
    if current_app.config.get('TEST_MODE'):
        # Mock response in test mode
        return {
            'success': True,
            'bank_name': 'Test Bank',
            'transaction_url': 'http://localhost:5001/transactions/b2b',
            'jwks_url': 'http://localhost:5001/transactions/jwks'
        }
    
    try:
        # Get the bank settings for API key
        bank_settings = BankSettings.query.first()
        if not bank_settings or not bank_settings.api_key:
            return {
                'success': False,
                'error': 'Bank not registered with Central Bank'
            }
        
        # Send the request to the Central Bank
        response = requests.get(
            f"{current_app.config.get('CENTRAL_BANK_URL')}/banks/{bank_prefix}",
            headers={
                'Authorization': f"Bearer {bank_settings.api_key}",
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'bank_name': data.get('bank_name'),
                'transaction_url': data.get('transaction_url'),
                'jwks_url': data.get('jwks_url')
            }
        else:
            return {
                'success': False,
                'error': f"Failed to get bank details: {response.text}"
            }
    except Exception as e:
        current_app.logger.error(f"Error getting bank details: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def validate_bank(bank_prefix):
    """Validate a bank with the Central Bank."""
    if current_app.config.get('TEST_MODE'):
        # Mock response in test mode
        return True
    
    try:
        # Get the bank details
        bank_details = get_bank_details(bank_prefix)
        return bank_details.get('success', False)
    except Exception as e:
        current_app.logger.error(f"Error validating bank: {str(e)}")
        return False
