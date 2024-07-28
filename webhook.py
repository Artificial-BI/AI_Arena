import os
import subprocess
import hmac
import hashlib
from flask import Blueprint, request, abort

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/hooks/update-ai-arena', methods=['POST'])
def webhook():
    secret = os.environ.get('SECRET_KEY')
    payload = request.get_data()
    received_signature = request.headers.get('X-Hub-Signature')
    computed_signature = hmac.new(secret.encode(), payload, hashlib.sha1).hexdigest()
    
    print(f"Payload received: {payload}")
    print(f"Payload received (decoded): {payload.decode('utf-8')}")
    print(f"1_Received signature: {received_signature}")
    print(f"2_Computed signature: {computed_signature}")
    
    received_signature = received_signature.split('=')[1] if received_signature else None
    if not hmac.compare_digest(computed_signature, received_signature):
        print("Signatures do not match!")
        abort(403)
    
    print("Signatures match. Processing webhook...")
    if request.headers.get('X-GitHub-Event') == 'push':
        return 'Webhook received and processed', 200
    return '', 400
