"""Gunicorn entry point — `gunicorn wsgi:app`."""
from mailer.config import Config, load_env
from mailer.webhook import create_app

load_env()
app = create_app(Config.from_env())
