# -*- encoding: utf-8 -*-

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps.chatbot.chat import get_response, preprocess_input
from flask import Blueprint, jsonify, request, redirect, url_for, flash

from apps.models import ChatHistory, Message
from apps import db

from apps.authentication.models import Users
from apps.authentication.util import hash_pass, verify_pass

import logging


@blueprint.route("/index")
@login_required
def index():

    return render_template("home/index.html", segment="index")


@blueprint.route("/<template>")
@login_required
def route_template(template):

    try:

        if not template.endswith(".html"):
            template += ".html"

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template("home/page-404.html"), 404

    except:
        return render_template("home/page-500.html"), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split("/")[-1]

        if segment == "":
            segment = "index"

        return segment

    except:
        return None


import json

# start of changes
predict_logger = logging.getLogger(__name__)


@blueprint.route("/predict", methods=["POST"])
def predict():
    predict_logger.debug("Entered predict route")
    data = request.get_json()
    user_input = data.get("message")
    user_id = data.get("user_id")

    if not user_input or not user_id:
        predict_logger.error("Missing message or user_id parameter")
        return jsonify({"error": "Missing message or user_id parameter"}), 400

    predict_logger.debug(f"User input: {user_input}")
    predict_logger.debug(f"User ID: {user_id}")

    cleaned_input = preprocess_input(user_input)
    response = get_response(cleaned_input)

    if current_user.is_authenticated:
        user_id = current_user.id

    # Get or create the chat history for the current user
    chat_history = ChatHistory.query.filter_by(user_id=user_id).first()
    if not chat_history:
        predict_logger.debug("Creating new chat history for user")
        chat_history = ChatHistory(user_id=user_id)
        db.session.add(chat_history)
        db.session.commit()  # Commit here to get an ID for the new chat history

    # Append the new message to the chat history
    new_message_user = Message(
        chat_history_id=chat_history.id, sender="user", message=user_input
    )
    new_message_bot = Message(
        chat_history_id=chat_history.id, sender="bot", message=response
    )
    db.session.add(new_message_user)
    db.session.add(new_message_bot)
    db.session.commit()

    predict_logger.debug(f"Response: {response}")

    return jsonify({"answer": response})


@blueprint.route('/new_chat', methods=['POST'])
def new_chat():
    user_id = request.form.get('user_id')
    if user_id:
        if current_user.is_authenticated:
            user_id = current_user.id

        # Save the current chat history to the database
        save_current_chat_history(user_id)

        # Create a new chat history for the user
        chat_history = ChatHistory(user_id=user_id)
        db.session.add(chat_history)
        db.session.commit()

    return jsonify({'success': True})


def save_current_chat_history(user_id):
    # Get the current chat history for the user
    current_chat_history = (
        ChatHistory.query.filter_by(user_id=user_id)
        .order_by(ChatHistory.id.desc())
        .first()
    )

    if current_chat_history:
        # Commit the current chat history to the database
        db.session.commit()


@blueprint.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    user_id = request.args.get('user_id')
    if user_id:
        if current_user.is_authenticated:
            user_id = current_user.id

        # Save the current chat history to the database
        save_current_chat_history(user_id)

        chat_history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.id.desc()).first()
        if chat_history:
            # Serialize the Message objects to a list of dictionaries
            messages = [{'id': message.id, 'text': message.message, 'timestamp': message.timestamp} for message in chat_history.messages]
            return jsonify({'messages': messages})
        else:
            return jsonify({'messages': []})
    else:
        return jsonify({'error': 'Missing user_id parameter'}), 400


from sqlalchemy.exc import IntegrityError
import pprint


@blueprint.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    print("========= update_profile route =========")
    pprint.pprint(request.form)  # Print the entire request form data

    username = request.form.get("username")
    print(f"username: {username}")

    email = request.form.get("email")
    print(f"email: {email}")

    current_password = request.form.get("current_password")
    print(f"current_password: {current_password}")

    new_password = request.form.get("new_password")
    print(f"new_password: {new_password}")

    # Get the current user's stored password hash
    stored_password_hash = current_user.password
    print(f"stored_password_hash: {stored_password_hash}")

    # Check if the provided current password matches the stored hash
    if not verify_pass(current_password, stored_password_hash):
        print("Invalid current password")
        return redirect(request.referrer or url_for("home"))

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

    return redirect(request.referrer or url_for("home"))


@blueprint.route("/get_current_user", methods=["GET"])
def get_current_user():
    if current_user.is_authenticated:
        user_data = {
            "username": current_user.username,
            "email": current_user.email,
            # Add any other user information you need
        }
        return jsonify(user_data)
    else:
        return jsonify({"error": "User not authenticated"}), 401


@blueprint.route("/check_current_password", methods=["POST"])
def check_current_password():
    # Get the current password from the request data
    current_password = request.form.get("current_password")

    # Get the current user's stored password hash
    stored_password_hash = current_user.password

    # Check if the provided current password matches the stored hash
    is_valid = verify_pass(current_password, stored_password_hash)

    return jsonify({"is_valid": is_valid})
