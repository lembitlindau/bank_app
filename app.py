import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///bank.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        BANK_PREFIX=os.environ.get('BANK_PREFIX', 'BNK'),
        CENTRAL_BANK_URL=os.environ.get('CENTRAL_BANK_URL', 'http://localhost:5001'),
        CENTRAL_BANK_API_KEY=os.environ.get('CENTRAL_BANK_API_KEY', 'test_api_key'),
        TEST_MODE=os.environ.get('TEST_MODE', 'False') == 'True'
    )

    # Override config with test config if passed
    if test_config:
        app.config.update(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    from .accounts import accounts_bp
    app.register_blueprint(accounts_bp)

    from .transactions import transactions_bp
    app.register_blueprint(transactions_bp)

    from .api import api_bp
    app.register_blueprint(api_bp)

    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)

    # Register CLI commands
    from .commands import register_commands
    register_commands(app)

    @app.route('/')
    def index():
        return 'Bank App is running!'

    return app
