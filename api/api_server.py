"""
EditEase API Server — Flask application factory.
Routes are organized into Blueprints under api/blueprints/.
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger

import config
from utils.logger import setup_logger
from api.blueprints import auth_bp, admin_bp, review_bp, media_bp

logger = setup_logger('api_server')


def create_app():
    app = Flask(__name__)
    CORS(app)
    Swagger(app)

    # Flask-Mail configuration (Gmail SMTP with App Password)
    app.config.update(
        MAIL_SERVER=config.MAIL_SERVER,
        MAIL_PORT=config.MAIL_PORT,
        MAIL_USE_TLS=config.MAIL_USE_TLS,
        MAIL_USERNAME=config.MAIL_USERNAME,
        MAIL_PASSWORD=config.MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER=config.MAIL_DEFAULT_SENDER,
    )
    from services.email_service import mail
    mail.init_app(app)

    # Register all domain blueprints
    app.register_blueprint(auth_bp)     # /register /login /logout /me
    app.register_blueprint(admin_bp)    # /admin/*
    app.register_blueprint(review_bp)   # /search /update_scene /review/bulk-update
    app.register_blueprint(media_bp)    # /upload /thumbnail /task_status /auto_organize ...

    @app.get('/health')
    def health():
        return jsonify({'ok': True, 'db': config.DB_NAME, 'collection': config.COLLECTION})

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=config.API_HOST, port=config.API_PORT, debug=config.API_DEBUG)
