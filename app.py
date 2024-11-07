from application import create_app
from application.celery_app import celery

app = create_app()
celery.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)
