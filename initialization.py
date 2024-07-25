from models import db
from default import add_default_values, remove_default_values

def init_db():
    db.create_all()
    add_default_values()
    # remove_default_values()  # Раскомментируйте, чтобы удалить значения по умолчанию
