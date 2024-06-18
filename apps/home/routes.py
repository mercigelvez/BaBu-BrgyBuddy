# -*- encoding: utf-8 -*-

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps.chatbot.chat import get_response, preprocess_input
from flask import Blueprint, jsonify, request, redirect, url_for, flash

from apps.models import ChatHistory
from apps import db

from apps.authentication.models import Users
from apps.authentication.util import hash_pass, verify_pass

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


from sqlalchemy.exc import IntegrityError
import pprint

@blueprint.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    print("========= update_profile route =========")
    pprint.pprint(request.form)  # Print the entire request form data

    username = request.form.get('username')
    print(f"username: {username}")

    email = request.form.get('email')
    print(f"email: {email}")

    current_password = request.form.get('current_password')
    print(f"current_password: {current_password}")

    new_password = request.form.get('new_password')
    print(f"new_password: {new_password}")

     # Get the current user's stored password hash
    stored_password_hash = current_user.password
    print(f"stored_password_hash: {stored_password_hash}")

    # Check if the provided current password matches the stored hash
    if not verify_pass(current_password, stored_password_hash):
        print("Invalid current password")
        return redirect(request.referrer or url_for('home'))

    try:
        # Update the user's information
        current_user.username = username
        current_user.email = email

        if new_password:
            current_user.password = hash_pass(new_password)

        # Save the changes to the database
        db.session.commit()
        print("Profile updated successfully")
    except IntegrityError:
        db.session.rollback()
        print("Username already exists. Please choose a different username.")

    return redirect(request.referrer or url_for('home'))


@blueprint.route('/get_current_user', methods=['GET'])
def get_current_user():
    if current_user.is_authenticated:
        user_data = {
            'username': current_user.username,
            'email': current_user.email,
            # Add any other user information you need
        }
        return jsonify(user_data)
    else:
        return jsonify({'error': 'User not authenticated'}), 401
    
    
@blueprint.route('/check_current_password', methods=['POST'])
def check_current_password():
    # Get the current password from the request data
    current_password = request.form.get('current_password')

    # Get the current user's stored password hash
    stored_password_hash = current_user.password

    # Check if the provided current password matches the stored hash
    is_valid = verify_pass(current_password, stored_password_hash)

    return jsonify({'is_valid': is_valid})