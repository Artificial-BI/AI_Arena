from extensions import db, migrate  # Импортируем расширения из extensions.py
from default import add_default_values, remove_default_values  # Импортируем функции для добавления и удаления значений по умолчанию

def init_extensions_and_db(app):
    """
    Функция для инициализации расширений Flask и базы данных.

    Args:
        app (Flask): Экземпляр приложения Flask.
    """
    db.init_app(app)  # Инициализация SQLAlchemy с экземпляром Flask приложения
    migrate.init_app(app, db)  # Инициализация Flask-Migrate с экземпляром Flask приложения и SQLAlchemy
    
    # Создаем контекст приложения для выполнения операций с базой данных
    with app.app_context():
        db.create_all()  # Создаем все таблицы в базе данных, которые определены в моделях
        #add_default_values()  # Добавляем значения по умолчанию в базу данных
        # remove_default_values()  # Раскомментируйте, чтобы удалить значения по умолчанию
