from extensions import db, migrate  # Import extensions from extensions.py
from default import add_default_values, remove_default_values  # Import functions to add and remove default values

def init_extensions_and_db(app):
    """
    Function to initialize Flask extensions and the database.

    Args:
        app (Flask): An instance of the Flask application.
    """
    db.init_app(app)  # Initialize SQLAlchemy with the Flask application instance
    migrate.init_app(app, db)  # Initialize Flask-Migrate with the Flask application instance and SQLAlchemy
    
    # Create an application context to perform database operations
    with app.app_context():
        db.create_all()  # Create all tables in the database that are defined in the models
        # add_default_values()  # Uncomment to add default values to the database
        # remove_default_values()  # Uncomment to remove default values
