# -*- encoding: utf-8 -*-

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from apps.chatbot.chat import get_response, preprocess_input
from flask import Blueprint, jsonify, request

from flask import jsonify, request
from apps.models import ChatHistory
from apps import db

@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
    

@blueprint.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Invalid JSON data'}), 400

    user_input = data.get('message')
    user_id = data.get('user_id')
    if not user_input or not user_id:
        return jsonify({'error': 'Missing message or user_id parameter'}), 400

    cleaned_input = preprocess_input(user_input)
    response = get_response(cleaned_input)

    # Save the chat history
    chat_history = ChatHistory.query.filter_by(user_id=user_id).first()
    if chat_history:
        chat_history.messages += f'User: {user_input}\nBot: {response}\n'
    else:
        chat_history = ChatHistory(user_id, f'User: {user_input}\nBot: {response}\n')
        db.session.add(chat_history)
    db.session.commit()

    return jsonify({'answer': response})


@blueprint.route('/new_chat', methods=['POST'])
def new_chat():
    user_id = request.form.get('user_id')
    if user_id:
        chat_history = ChatHistory.query.filter_by(user_id=user_id).first()
        if chat_history:
            chat_history.messages = ''  # Clear the current chat history
            db.session.commit()
    return jsonify({'success': True})


@blueprint.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    user_id = request.args.get('user_id')
    if user_id:
        chat_history = ChatHistory.query.filter_by(user_id=user_id).first()
        if chat_history:
            return jsonify({'messages': chat_history.messages})
    return jsonify({'messages': ''})