import json
import asyncio
from flask import Blueprint, request, jsonify, render_template, g
from extensions import db
from models import Message, Role
from gemini import GeminiAssistant
import logging

admin_bp = Blueprint('admin', __name__)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@admin_bp.route('/')
def arena():
    return render_template('arena.html')



@admin_bp.route('/update_settings', methods=['POST'])
def update_settings():
    temperature = request.form.get('temperature')
    top_p = request.form.get('top_p')
    top_k = request.form.get('top_k')
    return jsonify({'status': 'Settings updated'}), 200

@admin_bp.route('/send_message', methods=['POST'])
def send_message():
    try:
        content = request.form['message']
        role_name = request.form['role']  # Get role name from the form
        user_id = g.user.id  # Use the current user's ID

        # Create an assistant using the selected role
        assistant = GeminiAssistant(role_name)
        
        # Use asyncio.run to execute the asynchronous function
        #logger.info(f"Sending message to assistant: {content}")
        response = asyncio.run(assistant.send_message(content))
        #logger.info(f"Received response from assistant: {response}")

        # Save the message and response to the database
        message = Message(content=content, user_id=user_id)
        response_message = Message(content=response, user_id=0)
        db.session.add(message)
        db.session.add(response_message)
        db.session.commit()

        return jsonify({"status": "Message sent", "response": response})
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/get_instructions', methods=['POST'])
def get_instructions():
    try:
        role_name = request.form['role']
        role = Role.query.filter_by(name=role_name).first()
        if role:
            return jsonify({"instructions": role.instructions})
        else:
            return jsonify({"instructions": ""})
    except Exception as e:
        logger.error(f"Error fetching instructions: {e}")
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/save_instructions', methods=['POST'])
def save_instructions():
    try:
        role_name = request.form['role']
        instructions = request.form['instructions']
        logger.info(f"Saving instructions for role: {role_name}, instructions: {instructions}")
        
        role = Role.query.filter_by(name=role_name).first()
        if role:
            role.instructions = instructions
        else:
            role = Role(name=role_name, instructions=instructions)
            db.session.add(role)

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Error saving instructions: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@admin_bp.route('/admin', methods=['GET'])
def admin():
    messages = Message.query.all()
    return render_template('admin.html', messages=messages)

