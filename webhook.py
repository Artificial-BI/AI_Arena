from flask import Blueprint, request
import subprocess

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/hooks/update-ai-arena', methods=['POST'])
def webhook():
    if request.headers.get('X-GitHub-Event') == 'push':
        subprocess.call(['sh', '/home/xeon/AI_Arena/webhook_handler.sh'])
        return '', 200
    return '', 400
