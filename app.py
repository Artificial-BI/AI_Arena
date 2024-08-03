# --- app.py ---

from flask import Flask, render_template, request, g
from config import Config
from logging_config import configure_logging
from initialization import init_extensions_and_db  # Import the unified initialization function
from extensions import db
import traceback

app = Flask(__name__)
app.config.from_object(Config)

if not app.debug:
    configure_logging(app)

# Initialize extensions and the database
init_extensions_and_db(app)

# Import and register blueprints
from routes.index_routes import index_bp
from routes.common_routes import common_bp
from routes.player_routes import player_bp
from routes.viewer_routes import viewer_bp
from routes.admin_routes import admin_bp
from routes.arena_routes import arena_bp

app.register_blueprint(index_bp)
app.register_blueprint(common_bp, url_prefix='/common')
app.register_blueprint(player_bp, url_prefix='/player')
app.register_blueprint(viewer_bp, url_prefix='/viewer')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(arena_bp, url_prefix='/arena')

# Import and register the webhook blueprint
from webhook import webhook_bp
app.register_blueprint(webhook_bp)

# Add enumerate to Jinja2 environment
app.jinja_env.globals.update(enumerate=enumerate)

# Define error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    
    error_trace = traceback.format_exc()
    
    app.logger.error(f'Server Error: {error}, route: {request.url}')
    
    return render_template('500.html', error=error, error_trace=error_trace), 500

# Main entry point
if __name__ == "__main__":
    app.run(debug=True, port=5000)
