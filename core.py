from datetime import datetime
from models import db, Character, Arena, Tournament, TournamentMatch, Fight

class BattleManager:
    def __init__(self):
        pass

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
        fight = Fight(
            character1_id=character1_id,
            character2_id=character2_id,
            arena_id=arena_id,
            result=result,
            fight_date=datetime.now()
        )
        db.session.add(fight)
        db.session.commit()

class ArenaManager:
    def __init__(self):
        pass

    def create_arena(self, description, parameters):
        arena = Arena(description=description, parameters=parameters)
        db.session.add(arena)
        db.session.commit()

    def configure_arena(self, arena_id, parameters):
        arena = Arena.query.get(arena_id)
        if arena:
            arena.parameters = parameters
            db.session.commit()

class TournamentManager:
    def __init__(self):
        pass

    def create_tournament(self, name, format):
        tournament = Tournament(
            name=name,
            format=format,
            start_date=datetime.now(),
            end_date=None,
            current_stage='initial'
        )
        db.session.add(tournament)
        db.session.commit()

    def register_for_tournament(self, tournament_id, character_id):
        match = TournamentMatch(
            tournament_id=tournament_id,
            character_id=character_id,
            status='scheduled'
        )
        db.session.add(match)
        db.session.commit()

    def update_tournament(self, tournament_id, stage):
        tournament = Tournament.query.get(tournament_id)
        if tournament:
            tournament.current_stage = stage
            db.session.commit()
