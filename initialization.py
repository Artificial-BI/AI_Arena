from models import db
from default import add_default_values, remove_default_values

def init_db():
    db.create_all()
    # Uncomment the following line to add default values
    add_default_values()

    # Uncomment the following line to remove default values
    # remove_default_values()
