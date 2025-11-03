from application import create_app
from services.celery_app import celery

app = create_app()
celery.init_app(app)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("ENVIRONMENT", "development") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)