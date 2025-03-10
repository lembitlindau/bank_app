from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import jwt
import json
import base64
from flask import current_app

def generate_key_pair():
    """Generate an RSA key pair for JWT signing."""
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Serialize public key to PEM format
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_pem, public_pem

def load_private_key(private_key_pem):
    """Load a private key from PEM format."""
    return serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )

def load_public_key(public_key_pem):
    """Load a public key from PEM format."""
    return serialization.load_pem_public_key(
        public_key_pem.encode('utf-8'),
        backend=default_backend()
    )

def generate_jwt(payload, private_key_pem, kid='1'):
    """Generate a JWT token signed with the private key."""
    headers = {
        'alg': 'RS256',
        'kid': kid
    }
    
    return jwt.encode(
        payload=payload,
        key=private_key_pem,
        algorithm='RS256',
        headers=headers
    )

def verify_jwt(token, public_key_pem):
    """Verify a JWT token using the public key."""
    try:
        return jwt.decode(
            token,
            public_key_pem,
            algorithms=['RS256']
        )
    except jwt.InvalidTokenError as e:
        current_app.logger.error(f"JWT verification failed: {str(e)}")
        return None

def generate_jwks(public_key_pem, kid='1'):
    """Generate a JWKS (JSON Web Key Set) from a public key."""
    public_key = load_public_key(public_key_pem)
    
    # Get the public key in DER format
    public_numbers = public_key.public_numbers()
    
    # Convert to JWK format
    jwk = {
        'kty': 'RSA',
        'use': 'sig',
        'kid': kid,
        'alg': 'RS256',
        'n': base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, byteorder='big')).decode('utf-8').rstrip('='),
        'e': base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, byteorder='big')).decode('utf-8').rstrip('=')
    }
    
    return {'keys': [jwk]}
