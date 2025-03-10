import requests
import json
from flask import current_app
from datetime import datetime
import uuid

from ..models import Transaction, Account, BankSettings
from .. import db
from .crypto import generate_jwt, verify_jwt, load_public_key
from .central_bank import get_bank_details, validate_bank

def process_outgoing_transaction(account_from, account_to, amount, currency, explanation, sender_name):
    """Process an outgoing transaction to another bank."""
    try:
        # Create a transaction record with pending status
        transaction = Transaction(
            transaction_id=Transaction.generate_transaction_id(),
            account_from_id=account_from.id,
            account_to_external=account_to,
            amount=amount,
            currency=currency,
            explanation=explanation,
            status='pending',
            is_internal=False
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Extract the bank prefix from the destination account
        bank_prefix = account_to[:3]
        
        # Get the destination bank details from Central Bank
        bank_details = get_bank_details(bank_prefix)
        if not bank_details.get('success'):
            transaction.status = 'failed'
            transaction.error_message = f"Failed to get destination bank details: {bank_details.get('error')}"
            db.session.commit()
            return {
                'success': False,
                'error': transaction.error_message
            }
        
        # Get our bank settings
        bank_settings = BankSettings.query.first()
        if not bank_settings or not bank_settings.private_key:
            transaction.status = 'failed'
            transaction.error_message = "Bank not properly configured with keys"
            db.session.commit()
            return {
                'success': False,
                'error': transaction.error_message
            }
        
        # Prepare the transaction payload
        payload = {
            'accountFrom': account_from.account_number,
            'accountTo': account_to,
            'currency': currency,
            'amount': amount,
            'explanation': explanation,
            'senderName': sender_name
        }
        
        # Generate JWT with the transaction payload
        jwt_token = generate_jwt(payload, bank_settings.private_key)
        
        # Send the JWT to the destination bank's transaction endpoint
        if current_app.config.get('TEST_MODE'):
            # Mock response in test mode
            response_data = {'receiverName': 'Test Receiver'}
            response_status = 200
        else:
            response = requests.post(
                bank_details.get('transaction_url'),
                json={'jwt': jwt_token},
                headers={'Content-Type': 'application/json'}
            )
            response_data = response.json() if response.text else {}
            response_status = response.status_code
        
        # Process the response
        if response_status == 200:
            # Update transaction status and debit sender's account
            transaction.status = 'completed'
            transaction.completed_at = datetime.utcnow()
            transaction.receiver_name = response_data.get('receiverName')
            
            # Debit the sender's account
            account_from.balance -= amount
            
            db.session.commit()
            
            return {
                'success': True,
                'transaction_id': transaction.transaction_id,
                'receiver_name': transaction.receiver_name
            }
        else:
            # Update transaction status to failed
            transaction.status = 'failed'
            transaction.error_message = f"Transaction failed: {response_data.get('error', 'Unknown error')}"
            db.session.commit()
            
            return {
                'success': False,
                'error': transaction.error_message
            }
    except Exception as e:
        current_app.logger.error(f"Error processing outgoing transaction: {str(e)}")
        if transaction:
            transaction.status = 'failed'
            transaction.error_message = str(e)
            db.session.commit()
        
        return {
            'success': False,
            'error': str(e)
        }

def process_incoming_transaction(jwt_token):
    """Process an incoming transaction from another bank."""
    try:
        # Validate the JWT structure
        if not jwt_token:
            return {'error': 'Missing JWT token'}, 400
        
        # Extract the header to get the kid
        header = jwt_token.split('.')[0]
        header_data = json.loads(base64.b64decode(header + '==').decode('utf-8'))
        
        # Extract the payload without verification
        payload = jwt.decode(jwt_token, options={"verify_signature": False})
        
        # Verify the receiving account exists
        account_to = payload.get('accountTo')
        if not account_to:
            return {'error': 'Missing destination account'}, 400
        
        # Check if the account belongs to our bank
        bank_settings = BankSettings.query.first()
        if not bank_settings:
            return {'error': 'Bank not properly configured'}, 500
        
        if not account_to.startswith(bank_settings.bank_prefix):
            return {'error': 'Account does not belong to this bank'}, 400
        
        # Find the account in our database
        account = Account.query.filter_by(account_number=account_to).first()
        if not account:
            return {'error': 'Account not found'}, 404
        
        # Extract the sending bank prefix
        account_from = payload.get('accountFrom')
        if not account_from:
            return {'error': 'Missing source account'}, 400
        
        sending_bank_prefix = account_from[:3]
        
        # Validate the sending bank with Central Bank
        if not validate_bank(sending_bank_prefix):
            return {'error': 'Invalid sending bank'}, 400
        
        # Get the sending bank's JWKS endpoint
        bank_details = get_bank_details(sending_bank_prefix)
        if not bank_details.get('success'):
            return {'error': 'Failed to get sending bank details'}, 502
        
        # Retrieve the sending bank's public key from its JWKS endpoint
        if current_app.config.get('TEST_MODE'):
            # Mock response in test mode
            jwks_response = {'keys': [{'kid': header_data.get('kid'), 'n': '...', 'e': '...', 'kty': 'RSA', 'alg': 'RS256'}]}
            jwks_status = 200
        else:
            jwks_response = requests.get(bank_details.get('jwks_url')).json()
            jwks_status = 200  # Assuming successful response
        
        if jwks_status != 200:
            return {'error': 'Failed to retrieve sending bank public key'}, 502
        
        # Find the key with matching kid
        key = None
        for k in jwks_response.get('keys', []):
            if k.get('kid') == header_data.get('kid'):
                key = k
                break
        
        if not key:
            return {'error': 'Public key not found'}, 400
        
        # Convert JWK to PEM format (simplified for brevity)
        # In a real implementation, you would convert the JWK to PEM format
        # For this example, we'll assume we have a function to do this
        public_key_pem = convert_jwk_to_pem(key)  # This function would need to be implemented
        
        # Verify JWT signature using the public key
        try:
            verified_payload = verify_jwt(jwt_token, public_key_pem)
            if not verified_payload:
                return {'error': 'Invalid JWT signature'}, 400
        except Exception as e:
            return {'error': f'JWT verification failed: {str(e)}'}, 400
        
        # Create a transaction record
        transaction = Transaction(
            transaction_id=Transaction.generate_transaction_id(),
            account_to_id=account.id,
            account_to_external=account_from,
            amount=payload.get('amount'),
            currency=payload.get('currency'),
            explanation=payload.get('explanation'),
            status='completed',
            is_internal=False,
            completed_at=datetime.utcnow(),
            receiver_name=account.owner.full_name
        )
        
        # Credit the receiver's account
        account.balance += payload.get('amount')
        
        db.session.add(transaction)
        db.session.commit()
        
        # Return the receiver's name to the sending bank
        return {'receiverName': account.owner.full_name}, 200
    except Exception as e:
        current_app.logger.error(f"Error processing incoming transaction: {str(e)}")
        return {'error': str(e)}, 500

def convert_jwk_to_pem(jwk):
    """Convert a JWK to PEM format."""
    # This is a placeholder for the actual implementation
    # In a real application, you would implement this function
    # to convert a JWK to PEM format
    # For example, using the cryptography library
    return "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
