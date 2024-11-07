from celery import Celery
import flask

class FlaskCelery(Celery):
    def __init__(self, *args, **kwargs):
        super(FlaskCelery, self).__init__(*args, **kwargs)
        self.app = None
        self.patch_task()

    def patch_task(self):
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                if flask.has_app_context():
                    return TaskBase.__call__(self, *args, **kwargs)
                elif _celery.app is not None:
                    with _celery.app.app_context():
                        return TaskBase.__call__(self, *args, **kwargs)
                else:
                    raise RuntimeError("App context is not available. Ensure `init_app` is called.")

        self.Task = ContextTask

    def init_app(self, app):
        self.app = app
        self.conf.update(
            broker_url=app.config['CELERY_BROKER_URL'],
            result_backend=app.config['CELERY_RESULT_BACKEND']
        )

celery = FlaskCelery()
