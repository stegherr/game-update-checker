"""Flask app factory"""
from flask import Flask

def create_app():
    """ Create a Flask app """
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static',
                static_url_path='/static')
    app.config.from_object('app.config.Config')

    with app.app_context():
        # Import routes after app creation to avoid circular imports
        from app.routes import register_routes
        register_routes(app)

    return app
