from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_security import Security, SQLAlchemyUserDatastore
from flask_caching import Cache
import redis

from application.database import *
from application.models import *
from route import init_app as init_routes


def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./mad2.sqlite3'
    app.config['SECRET_KEY'] = 'madthemad2'
    app.config['SECURITY_PASSWORD_SALT'] = 'madthemad2salt'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SECURITY_CHANGEABLE'] = True
    app.config['SECURITY_CHANGE_URL'] = '/change_password'
    app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = True
    app.config['SECURITY_CHANGEABLE'] = True
    app.config['SECURITY_SEND_PASSWORD_CHANGE_EMAIL'] = True
    app.config['SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE'] = "Your email has been changed"

    app.config['JWT_SECRET_KEY'] = 'madthemad2jwt'
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_REDIS_PORT'] = 6379
    app.config['CACHE_REDIS_DB'] = 0
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300

    cache = Cache(app=app)

    db.init_app(app)
    cache.init_app(app)

    app.redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

    jwt = JWTManager(app)
    app.jwt = jwt

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    migrate = Migrate(app, db)

    with app.app_context():
        db.create_all()
        print(f"Registered Models: {db.metadata.tables.keys()}")

    print(f"SQLite database path: {app.config['SQLALCHEMY_DATABASE_URI']}")

    init_routes(app)

    @app.jwt.token_in_blocklist_loader()
    def check_if_token_in_blacklist(jwt_payload):
        jti = jwt_payload['jti']
        return app.redis_client.get(f"blacklist:{jti}") is not None

    return app
