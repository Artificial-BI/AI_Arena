from extensions import db, migrate
from default import add_default_values

def init_extensions_and_db(app):
    """
    Function to initialize Flask extensions and the database.

    Args:
        app (Flask): An instance of the Flask application.
    """
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()
        add_default_values()
