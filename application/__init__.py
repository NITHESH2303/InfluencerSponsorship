import click
import redis
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
    app = Flask(__name__, template_folder= "/Users/nithesh-pt7363/Work/Platform/InfluencerSponsorship/templates")
    print(app.template_folder)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./mad2.sqlite3'
    app.config['SECRET_KEY'] = 'MadTheMad2'
    app.config['SECURITY_PASSWORD_SALT'] = 'SecretOfMadTheMad2'
    app.config['SECURITY_PASSWORD_HASH'] = 'argon2'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SECURITY_CHANGEABLE'] = True
    app.config['SECURITY_CHANGE_URL'] = '/change_password'
    app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = True
    app.config['SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE'] = "Your email has been changed"

    app.config['JWT_SECRET_KEY'] = 'MadTheMad2'
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_SECURE'] = False
    app.config['JWT_REFRESH_TOKEN_IN_COOKIE'] = True
    app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
    # TODO : configure for CSFR
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/refresh'

    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_REDIS_PORT'] = 6379
    app.config['CACHE_REDIS_DB'] = 0
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 1800

    app.config['CELERY_BROKER_URL'] = 'redis://127.0.0.1:6379/1'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://127.0.0.1:6379/1'

    app.config['EXPORT_FOLDER'] = "/Users/nithesh-pt7363/Work/Platform/InfluencerSponsorship/export"

    # logging.basicConfig(level=logging.INFO)

    cors = CORS(app, resources={
        r"/api/*": {
            "origins": "http://localhost:5173",
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    cache = Cache(app=app)

    try:
        app.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        app.redis_client.ping()
    except redis.ConnectionError:
        print("Could not connect to Redis. Please ensure that Redis is running.")

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

    print(f"SQLite database path: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # @app.before_request
    # def handle_options():
    #     if request.method == "OPTIONS":
    #         response = make_response()
    #         response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
    #         response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
    #         response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    #         response.headers.add("Access-Control-Allow-Credentials", "true")
    #         return response

    @app.before_request
    def load_roles_from_jwt():
        try:
            verify_jwt_in_request(optional=True)
            claims = get_jwt()
            # print(claims)
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