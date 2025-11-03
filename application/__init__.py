import click
import redis
import os
from flask import Flask, g
from flask_caching import Cache
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt
from flask_migrate import Migrate
from flask_security import Security, SQLAlchemyUserDatastore

from application.PreProcess import PreProcess
from application.database import *
from application.models import User, Role
from routes.blueprint import init_app as init_routes


def create_app():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
    EXPORT_DIR = os.environ.get('EXPORT_FOLDER', '/tmp/export')
    app = Flask(__name__, template_folder= TEMPLATE_DIR)
    print(app.template_folder)

    # Database Configuration - Use PostgreSQL for production
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///./mad2.sqlite3'
    ).replace('postgres://', 'postgresql://')  # Fix for Render's postgres:// URL
    
    # Security Keys - MUST be environment variables in production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'MadTheMad2')
    app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', 'SecretOfMadTheMad2')
    app.config['SECURITY_PASSWORD_HASH'] = 'argon2'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SECURITY_CHANGEABLE'] = True
    app.config['SECURITY_CHANGE_URL'] = '/change_password'
    app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = True
    app.config['SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE'] = "Your email has been changed"

    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'MadTheMad2')
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    # Set to True in production (HTTPS)
    app.config['JWT_COOKIE_SECURE'] = os.environ.get('ENVIRONMENT', 'development') == 'production'
    app.config['JWT_REFRESH_TOKEN_IN_COOKIE'] = True
    app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/refresh'

    # Redis Configuration - Use environment variable for production
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_REDIS_URL'] = f"{redis_url}/0"
    app.config['CACHE_DEFAULT_TIMEOUT'] = 1800

    app.config['CELERY_BROKER_URL'] = f"{redis_url}/1"
    app.config['CELERY_RESULT_BACKEND'] = f"{redis_url}/1"

    app.config['EXPORT_FOLDER'] = EXPORT_DIR

    # CORS Configuration - Use environment variable for production
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    cors = CORS(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    cache = Cache(app=app)

    # Redis Client Connection
    try:
        # Parse Redis URL for connection
        from urllib.parse import urlparse
        parsed = urlparse(redis_url)
        app.redis_client = redis.StrictRedis(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 6379,
            password=parsed.password,
            db=0,
            decode_responses=True
        )
        app.redis_client.ping()
    except redis.ConnectionError as e:
        print(f"Could not connect to Redis: {e}. Please ensure that Redis is running.")

    jwt = JWTManager(app)
    app.jwt = jwt

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    migrate = Migrate(app, db)

    with app.app_context():
        db.init_app(app)
        cache.init_app(app)
        init_routes(app)
        try:
            db.create_all()
            print(f"Registered Models: {db.metadata.tables.keys()}")
            PreProcess()
        except Exception as e:
            print(f"Error during database initialization: {e}")

    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    @app.before_request
    def load_roles_from_jwt():
        try:
            verify_jwt_in_request(optional=True)
            claims = get_jwt()
            g.roles = claims.get("role", [])
        except Exception as e:
            g.roles = []

    @app.cli.command('reset-db')
    @click.confirmation_option(prompt='Are you sure you want to reset the database?')
    def reset_db():
        db.drop_all()
        db.create_all()
        PreProcess()
        click.echo('Database has been reset...')

    @app.jwt.token_in_blocklist_loader
    def check_if_token_in_blacklist(jwt_header, jwt_payload):
        jti = jwt_payload['jti']
        return app.redis_client.get(f"blacklist:{jti}") is not None

    return app