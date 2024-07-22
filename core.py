# core.py
import sqlite3
from datetime import datetime
from models import get_db_connection

class BattleManager:
    def __init__(self):
        self.connection = get_db_connection()

    def organize_battle(self, character1_id, character2_id, arena_id):
        # Логика проведения боя
        result = self.evaluate_battle(character1_id, character2_id)
        self.save_battle(character1_id, character2_id, arena_id, result)

    def evaluate_battle(self, character1_id, character2_id):
        # Логика оценки боя
        # Здесь будет взаимодействие с нейросетью "рефери"
        result = "draw"  # Пример
        return result

    def save_battle(self, character1_id, character2_id, arena_id, result):
        with self.connection as conn:
            conn.execute(
                'INSERT INTO fights (character1_id, character2_id, arena_id, result, fight_date) VALUES (?, ?, ?, ?, ?)',
                (character1_id, character2_id, arena_id, result, datetime.now())
            )

class ArenaManager:
    def __init__(self):
        self.connection = get_db_connection()

    def create_arena(self, description, parameters):
        with self.connection as conn:
            conn.execute(
                'INSERT INTO arenas (description, parameters) VALUES (?, ?)',
                (description, parameters)
            )

    def configure_arena(self, arena_id, parameters):
        with self.connection as conn:
            conn.execute(
                'UPDATE arenas SET parameters = ? WHERE id = ?',
                (parameters, arena_id)
            )

class TournamentManager:
    def __init__(self):
        self.connection = get_db_connection()

    def create_tournament(self, name, format):
        with self.connection as conn:
            conn.execute(
                'INSERT INTO tournaments (name, format, start_date, end_date, current_stage) VALUES (?, ?, ?, ?, ?)',
                (name, format, datetime.now(), None, 'initial')
            )

    def register_for_tournament(self, tournament_id, character_id):
        with self.connection as conn:
            conn.execute(
                'INSERT INTO tournament_matches (tournament_id, character_id, status) VALUES (?, ?, ?)',
                (tournament_id, character_id, 'scheduled')
            )

    def update_tournament(self, tournament_id, stage):
        with self.connection as conn:
            conn.execute(
                'UPDATE tournaments SET current_stage = ? WHERE id = ?',
                (stage, tournament_id)
            )
