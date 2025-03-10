import click
from flask.cli import with_appcontext
from ..models import User, Account, Transaction
from .. import db
from ..utils.crypto import generate_key_pair

def register_commands(app):
    """Register custom commands for the Flask CLI."""
    
    @app.cli.command('init-db')
    @with_appcontext
    def init_db_command():
        """Initialize the database."""
        db.create_all()
        click.echo('Initialized the database.')
    
    @app.cli.command('generate-keys')
    @with_appcontext
    def generate_keys_command():
        """Generate RSA key pair for the bank."""
        private_key, public_key = generate_key_pair()
        click.echo('Generated RSA key pair.')
        click.echo(f'Private key: {private_key[:20]}...')
        click.echo(f'Public key: {public_key[:20]}...')
    
    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('password')
    @with_appcontext
    def create_admin_command(username, password):
        """Create an admin user."""
        user = User(username=username, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Created admin user: {username}')
    
    @app.cli.command('register-bank')
    @with_appcontext
    def register_bank_command():
        """Register the bank with the Central Bank."""
        from ..utils.central_bank import register_with_central_bank
        result = register_with_central_bank()
        if result.get('success'):
            click.echo('Successfully registered with Central Bank.')
            click.echo(f'Bank prefix: {result.get("bank_prefix")}')
            click.echo(f'API key: {result.get("api_key")}')
        else:
            click.echo(f'Failed to register with Central Bank: {result.get("error")}')
