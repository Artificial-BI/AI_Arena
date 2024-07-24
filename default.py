# file: default.py

from models import db, User, Character, Message, RefereePrompt, CommentatorPrompt, Fight, Arena, Tournament, TournamentMatch, Role, Player, TopPlayer

def add_default_values():
    # Check if default users exist
    if not User.query.filter_by(username='default_user').first():
        default_user = User(username='default_user', role='player', name='Default User', email='default@example.com', password='password')
        db.session.add(default_user)
        db.session.commit()

    if not User.query.filter_by(username='admin_user').first():
        admin_user = User(username='admin_user', role='admin', name='Admin User', email='admin@example.com', password='adminpassword')
        db.session.add(admin_user)
        db.session.commit()

    # Check if default players exist
    if not Player.query.filter_by(name='default_player').first():
        default_player = Player(name='default_player')
        db.session.add(default_player)
        db.session.commit()

    # Check if default characters exist
    if not Character.query.filter_by(name='default_character').first():
        default_character = Character(
            user_id=default_user.id if 'default_user' in locals() else 1,
            player_id=default_player.id if 'default_player' in locals() else 1,
            name='default_character',
            description='This is a default character.',
            image_url='http://example.com/default.png',
            health_points=100,
            is_alive=True,
            traits='default traits'
        )
        db.session.add(default_character)
        db.session.commit()

    # Check if default messages exist
    if not Message.query.filter_by(content='default_message').first():
        default_message = Message(user_id=default_user.id if 'default_user' in locals() else 1, content='default_message')
        db.session.add(default_message)
        db.session.commit()

    # Check if default referee prompts exist
    if not RefereePrompt.query.filter_by(prompt_text='default_referee_prompt').first():
        default_referee_prompt = RefereePrompt(prompt_text='default_referee_prompt')
        db.session.add(default_referee_prompt)
        db.session.commit()

    # Check if default commentator prompts exist
    if not CommentatorPrompt.query.filter_by(prompt_text='default_commentator_prompt').first():
        default_commentator_prompt = CommentatorPrompt(prompt_text='default_commentator_prompt')
        db.session.add(default_commentator_prompt)
        db.session.commit()

    # Check if default fights exist
    if not Fight.query.filter_by(result='default_result').first():
        default_fight = Fight(character1_id=1, character2_id=2, arena_id=1, result='default_result')
        db.session.add(default_fight)
        db.session.commit()

    # Check if default arenas exist
    if not Arena.query.filter_by(description='default_arena').first():
        default_arena = Arena(description='default_arena', parameters='default_parameters')
        db.session.add(default_arena)
        db.session.commit()

    # Check if default tournaments exist
    if not Tournament.query.filter_by(name='default_tournament').first():
        default_tournament = Tournament(name='default_tournament', format='single elimination', start_date=datetime.utcnow())
        db.session.add(default_tournament)
        db.session.commit()

    # Check if default tournament matches exist
    if not TournamentMatch.query.filter_by(status='default_status').first():
        default_tournament_match = TournamentMatch(tournament_id=default_tournament.id if 'default_tournament' in locals() else 1, character_id=1, status='default_status')
        db.session.add(default_tournament_match)
        db.session.commit()

    # Check if default roles exist
    if not Role.query.filter_by(name='default_role').first():
        default_role = Role(name='default_role', instructions='default_instructions')
        db.session.add(default_role)
        db.session.commit()

    # Check if default top players exist
    if not TopPlayer.query.filter_by(name='default_top_player').first():
        default_top_player = TopPlayer(name='default_top_player', wins=10, losses=5, character_name='default_character', weekly_wins=2, weekly_losses=1)
        db.session.add(default_top_player)
        db.session.commit()

def remove_default_values():
    # Remove default users
    default_user = User.query.filter_by(username='default_user').first()
    if default_user:
        db.session.delete(default_user)
        db.session.commit()
    
    admin_user = User.query.filter_by(username='admin_user').first()
    if admin_user:
        db.session.delete(admin_user)
        db.session.commit()
    
    # Remove default players
    default_player = Player.query.filter_by(name='default_player').first()
    if default_player:
        db.session.delete(default_player)
        db.session.commit()

    # Remove default characters
    default_character = Character.query.filter_by(name='default_character').first()
    if default_character:
        db.session.delete(default_character)
        db.session.commit()

    # Remove default messages
    default_message = Message.query.filter_by(content='default_message').first()
    if default_message:
        db.session.delete(default_message)
        db.session.commit()

    # Remove default referee prompts
    default_referee_prompt = RefereePrompt.query.filter_by(prompt_text='default_referee_prompt').first()
    if default_referee_prompt:
        db.session.delete(default_referee_prompt)
        db.session.commit()

    # Remove default commentator prompts
    default_commentator_prompt = CommentatorPrompt.query.filter_by(prompt_text='default_commentator_prompt').first()
    if default_commentator_prompt:
        db.session.delete(default_commentator_prompt)
        db.session.commit()

    # Remove default fights
    default_fight = Fight.query.filter_by(result='default_result').first()
    if default_fight:
        db.session.delete(default_fight)
        db.session.commit()

    # Remove default arenas
    default_arena = Arena.query.filter_by(description='default_arena').first()
    if default_arena:
        db.session.delete(default_arena)
        db.session.commit()

    # Remove default tournaments
    default_tournament = Tournament.query.filter_by(name='default_tournament').first()
    if default_tournament:
        db.session.delete(default_tournament)
        db.session.commit()

    # Remove default tournament matches
    default_tournament_match = TournamentMatch.query.filter_by(status='default_status').first()
    if default_tournament_match:
        db.session.delete(default_tournament_match)
        db.session.commit()

    # Remove default roles
    default_role = Role.query.filter_by(name='default_role').first()
    if default_role:
        db.session.delete(default_role)
        db.session.commit()

    # Remove default top players
    default_top_player = TopPlayer.query.filter_by(name='default_top_player').first()
    if default_top_player:
        db.session.delete(default_top_player)
        db.session.commit()
