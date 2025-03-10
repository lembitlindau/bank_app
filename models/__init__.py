from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

from .. import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accounts = db.relationship('Account', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(64), unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    balance = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='EUR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    sent_transactions = db.relationship('Transaction', 
                                       foreign_keys='Transaction.account_from_id',
                                       backref='sender', lazy='dynamic')
    received_transactions = db.relationship('Transaction', 
                                           foreign_keys='Transaction.account_to_id',
                                           backref='receiver', lazy='dynamic')
    
    @staticmethod
    def generate_account_number(bank_prefix):
        """Generate a unique account number with the bank prefix."""
        unique_id = uuid.uuid4().hex
        return f"{bank_prefix}{unique_id}"
    
    def __repr__(self):
        return f'<Account {self.account_number}>'


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(64), unique=True, index=True)
    account_from_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    account_to_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=True)
    account_to_external = db.Column(db.String(64), nullable=True)
    amount = db.Column(db.Float)
    currency = db.Column(db.String(3))
    explanation = db.Column(db.String(256))
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_internal = db.Column(db.Boolean, default=True)
    receiver_name = db.Column(db.String(128), nullable=True)
    error_message = db.Column(db.String(256), nullable=True)
    
    @staticmethod
    def generate_transaction_id():
        """Generate a unique transaction ID."""
        return uuid.uuid4().hex
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'


class BankSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(128))
    bank_prefix = db.Column(db.String(3), unique=True)
    api_key = db.Column(db.String(64))
    transaction_url = db.Column(db.String(256))
    jwks_url = db.Column(db.String(256))
    private_key = db.Column(db.Text)
    public_key = db.Column(db.Text)
    central_bank_url = db.Column(db.String(256))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BankSettings {self.bank_name}>'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
